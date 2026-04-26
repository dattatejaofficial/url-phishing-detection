import io
import os
import json
import pandas as pd
from datetime import timedelta, timezone

from pymongo import MongoClient

from azure.storage.blob import BlobServiceClient

from monitoring_entity import MonitoringConfig
from monitoring_utils import *
from retraining_controller.controller import evaluate_and_trigger

monitoring_config = MonitoringConfig()

ANCHOR_DATE = monitoring_config.start_date.replace(tzinfo=timezone.utc)

FEATURES = read_yaml_file(monitoring_config.active_features_data_schema_path)['active_features']
LABELS = read_yaml_file(monitoring_config.active_features_data_schema_path)['labels']

MONGO_CLIENT = MongoClient(os.getenv("MONGODB_URI"))

def get_rolling_window():
    now = monitoring_config.current_time

    days_since_anchor = (now - ANCHOR_DATE).days
    interval_number = days_since_anchor // monitoring_config.no_of_days
    should_run = (days_since_anchor % monitoring_config.no_of_days) == 0

    start = ANCHOR_DATE + timedelta(days = interval_number * monitoring_config.no_of_days)
    end = start + timedelta(days = monitoring_config.no_of_days)

    return start, end, should_run

def fetch_data():
    db = MONGO_CLIENT[monitoring_config.database_name]
    
    feedback_collection = db[monitoring_config.feedback_collection_name]
    reference_collection = db[monitoring_config.current_collection_name]

    start_time, end_time, should_run_monitoring = get_rolling_window()

    if not should_run_monitoring:
        print('Skipping monitoring - window completed')
        return None, None, None

    query = {
        "created_at" : {
            "$gte" : start_time,
            "$lt" : end_time
        }
    }

    feedback_projection = {f:1 for f in FEATURES + LABELS}
    feedback_projection['_id'] = 0

    reference_projection = {f:1 for f in FEATURES}
    reference_projection['_id'] = 0

    feedback_docs = list(feedback_collection.find(query, feedback_projection))
    reference_docs = list(reference_collection.find({}, reference_projection))
    
    if not feedback_docs or not reference_docs:
        print("No documents found for monitoring")
        return None, None, None
    
    feedback_df = pd.DataFrame(feedback_docs)
    reference_df = pd.DataFrame(reference_docs)
    
    features_df = feedback_df.reindex(columns=FEATURES)
    predictions_df = feedback_df.reindex(columns=LABELS)

    return features_df, predictions_df, reference_df

def run_drift(features_df, reference_df):
    drift_report = compute_drift_report(reference_df, features_df, FEATURES)

    return {
        "window" : f"{monitoring_config.no_of_days}_day_strict_interval",
        "feature_drift" : drift_report,
        "computed_at" : monitoring_config.current_time.isoformat()
    }

def run_volume(features_df, reference_df):
    volume_report = compute_data_volume(len(features_df), len(reference_df))

    return volume_report

def upload_to_blob(reports : dict):
    conn_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    container_name = os.getenv('AZURE_BLOB_CONTAINER')

    if not conn_str or not container_name:
        raise ValueError('Azure connection not configured')
    
    blob_service = BlobServiceClient.from_connection_string(conn_str)
    container_client = blob_service.get_container_client(container_name)

    paths = {
        monitoring_config.drift_task_report_path : reports['drift'],
        monitoring_config.volume_task_report_path : reports['volume'],
        monitoring_config.retraining_decision_report_path : reports['trigger_retraining']
    }

    for blob_name, content in paths.items():
        if content is None:
            continue

        buffer = io.BytesIO(json.dumps(content,indent=4).encode('utf-8'))
        container_client.upload_blob(name=blob_name, data=buffer, overwrite=True)

def run_monitoring():
    features_df, _, reference_df = fetch_data()

    if features_df is None or reference_df is None:
        print('Skipping monitoring - no data')
        return None, None
    
    drift_report = run_drift(features_df, reference_df)
    volume_report = run_volume(features_df, reference_df)

    reports = {
        "drift" : drift_report,
        "volume" : volume_report
    }

    decision = evaluate_and_trigger(reports)
    reports['trigger_retraining'] = decision
    upload_to_blob(reports)

    return reports, decision