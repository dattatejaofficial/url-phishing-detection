import io
import os
import json
import pandas as pd
from datetime import datetime, timedelta, timezone

from pymongo import MongoClient

from azure.storage.blob import BlobServiceClient

from monitoring_entity import MonitoringConfig
from monitoring_utils import read_yaml_file, compute_drift_report, compute_data_volume, compute_performance_metrics

monitoring_config = MonitoringConfig()

ANCHOR_DATE = monitoring_config.start_date.replace(tzinfo=timezone.utc)

def get_rolling_window():
    now = monitoring_config.timestamp

    days_since_anchor = (now - ANCHOR_DATE).days
    interval_number = days_since_anchor // 15

    start = ANCHOR_DATE + timedelta(days=interval_number * 15)
    end = start + timedelta(days=15)

    return start, end

def fetch_data():
    uri = os.getenv('MONGODB_URI')
    if not uri:
        raise ValueError('MonogoDB Connection not configured')
    client = MongoClient(uri)
    db = client[monitoring_config.database_name]
    
    feedback_collection = db[monitoring_config.feedback_collection_name]
    reference_collection = db[monitoring_config.current_collection_name]

    start_time, end_time = get_rolling_window()

    query = {
        "created_at" : {
            "$gte" : start_time,
            "$lt" : end_time
        }
    }
    feedback_docs = list(feedback_collection.find(query))
    reference_docs = list(reference_collection.find({}))
    
    if not feedback_docs or not reference_docs:
        print("No documents found for monitoring")
        return None, None, None
    
    feedback_df = pd.DataFrame(feedback_docs)
    feedback_df.drop(columns=["_id"], inplace=True)

    reference_df = pd.DataFrame(reference_docs)
    reference_df.drop(columns=['_id'], inplace=True)

    features = read_yaml_file(monitoring_config.active_features_data_schema_path)['active_features']
    
    features_df = feedback_df[features]
    predictions_df = features_df.drop(columns=features)

    return features_df, predictions_df, reference_df

def run_drift(features_df, reference_df):
    active_features = read_yaml_file(monitoring_config.active_features_data_schema_path)['active_features']
    drift_report = compute_drift_report(reference_df, features_df, active_features)

    return {
        "window" : f"{monitoring_config.no_of_days}_day_strict_interval",
        "feature_drift" : drift_report,
        "computed_at" : datetime.now(timezone.utc).isoformat()
    }

def run_performance(predictions_df):
    metrics = compute_performance_metrics(predictions_df)

    return {
        'window' : f"{monitoring_config.no_of_days}_day_strict_interval",
        **metrics
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
        monitoring_config.performance_report_path : reports['performance'],
        monitoring_config.volume_task_report_path : reports['volume']
    }

    for blob_name, content in paths.items():
        if content is None:
            continue

        buffer = io.BytesIO(json.dumps(content,indent=4).encode('utf-8'))
        container_client.upload_blob(name=blob_name, data=buffer, overwrite=True)

def run_monitoring():
    features_df, predictions_df, reference_df = fetch_data()

    if features_df is None or reference_df is None:
        print('Skipping monitoring - no data')
        return None
    
    drift_report = run_drift(features_df, reference_df)
    performance_report = run_performance(predictions_df)
    volume_report = run_volume(features_df, reference_df)

    reports = {
        "drift" : drift_report,
        "performance" : performance_report,
        "volume" : volume_report
    }

    upload_to_blob(reports)

    return reports