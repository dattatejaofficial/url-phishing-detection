import os
from datetime import datetime
from phishingsystem.constants import training_pipeline

class TrainingPipelineConfig:
    def __init__(self, timestamp = datetime.now()):
        timestamp = timestamp.strftime('%d_%m_%Y_%H_%M_%S')
        self.pipeline_name : str = training_pipeline.PIPELINE_NAME
        self.artifact_name : str = training_pipeline.ARTIFACT_NAME
        self.artifact_dir : str = os.path.join(self.artifact_name,timestamp)

class DataPreparationConfig:
    def __init__(self, training_pipeline_config : TrainingPipelineConfig):
        self.data_preparation_dir : str = os.path.join(
            training_pipeline_config.artifact_dir,
            training_pipeline.DATA_PREPARATION_DIR_NAME
        )
        self.raw_data_path : str = training_pipeline.RAW_DATA_PATH
        self.processed_data_path : str = os.path.join(
            self.data_preparation_dir,
            training_pipeline.DATA_PREPARATION_PROCESSED_DIR_NAME,
            training_pipeline.PROCESSED_DATA_PATH
        )
        self.original_url_column_name : str = training_pipeline.ORIGINAL_URL_COLUMN_NAME
        self.processed_url_column_name : str = training_pipeline.PROCESSED_URL_COLUMN_NAME
        self.target_column_name : str = training_pipeline.TARGET_COLUMN_NAME