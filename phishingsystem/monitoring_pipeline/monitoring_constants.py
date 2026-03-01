import os
from datetime import datetime, timezone

ACTIVE_FEATURES_DATA_SCHEMA_PATH = os.path.join("data_schema","features_config.yaml")

ANCHOR_DATE = datetime(2026,3,1, tzinfo=timezone.utc)

MONGODB_DATABASE_NAME = "URLPhishingSystem"
MONGODB_FEEDBACK_COLLECTION_NAME = "FeedbackURLs"
MONGODB_CURRENT_COLLECTION_NAME = 'URLStructuralFeatures'

DRIFT_TASK_DIR = "drift_task"
DRIFT_TASK_REPORT_PATH = "drift_report.json"

PERFORMANCE_TASK_DIR = "performance_task"
PERFORMANCE_TASK_REPORT_PATH = "performance_report.json"

VOLUME_TASK_DIR = "volume_task"
VOLUME_TASK_REPORT_PATH = "volume_report.json"

RECALL_THRESHOLD = 0.97
SEVERE_PSI_THRESHOLD = 0.3
PSI_THRESHOLD = 0.2
VOLUME_RATIO_THRESHOLD = 0.4

ENABLE_DRIFT_TRIGGER = True
ENABLE_PERFORMANCE_TRIGGER = True
ENABLE_VOLUME_TRIGGER = True