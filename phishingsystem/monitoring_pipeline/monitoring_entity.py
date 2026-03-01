import os
from datetime import datetime, timezone
import monitoring_constants

class MonitoringConfig:
    def __init__(self, timestamp = datetime.now(timezone.utc)):
        timestamp = timestamp.strftime("%d_%m_%Y_%H_%M_%S")
        self.timestamp = timestamp

        self.start_date = monitoring_constants.ANCHOR_DATE
        
        self.database_name = monitoring_constants.MONGODB_DATABASE_NAME
        self.feedback_collection_name = monitoring_constants.MONGODB_FEEDBACK_COLLECTION_NAME
        self.current_collection_name = monitoring_constants.MONGODB_CURRENT_COLLECTION_NAME

        self.active_features_data_schema_path = monitoring_constants.ACTIVE_FEATURES_DATA_SCHEMA_PATH

        self.drift_task_report_path = os.path.join(
            self.timestamp,
            monitoring_constants.DRIFT_TASK_DIR,
            monitoring_constants.DRIFT_TASK_REPORT_PATH
        )

        self.performance_report_path = os.path.join(
            self.timestamp,
            monitoring_constants.PERFORMANCE_TASK_DIR,
            monitoring_constants.PERFORMANCE_TASK_REPORT_PATH
        )

        self.volume_task_report_path = os.path.join(
            self.timestamp,
            monitoring_constants.VOLUME_TASK_DIR,
            monitoring_constants.VOLUME_TASK_REPORT_PATH
        )