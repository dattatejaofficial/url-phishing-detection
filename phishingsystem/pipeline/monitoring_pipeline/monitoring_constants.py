import os
from datetime import datetime, timezone

ACTIVE_FEATURES_DATA_SCHEMA_PATH = os.path.join("data_schema","features_config.yaml")

ANCHOR_DATE = datetime(2026,3,1, tzinfo=timezone.utc)
NUMBER_OF_DAYS = 15

MONGODB_DATABASE_NAME = "URLPhishingSystem"
MONGODB_FEEDBACK_COLLECTION_NAME = "FeedbackURLs"
MONGODB_CURRENT_COLLECTION_NAME = 'URLStructuralFeatures'

DRIFT_TASK_DIR = "drift_task"
DRIFT_TASK_REPORT_PATH = "drift_report.json"

VOLUME_TASK_DIR = "volume_task"
VOLUME_TASK_REPORT_PATH = "volume_report.json"

RETRAINING_DECISION_REPORT_DIR = 'retraining_decision'
RETRAINING_DECISION_REPORT_PATH = 'decision'

SEVERE_PSI_THRESHOLD = 0.3
PSI_THRESHOLD = 0.2
VOLUME_RATIO_THRESHOLD = 0.4

ENABLE_DRIFT_TRIGGER = True
ENABLE_VOLUME_TRIGGER = True

RETRAINING_WORKFLOW_FILE = '.github/workflows/retraining_workflow.yml'
GITHUB_BRANCH = 'main'