import os
from datetime import datetime
from phishingsystem.constants import training_pipeline
from phishingsystem.entity.artifact_entity import FeatureExtractionArtifact, DataValidationArtifact, DataPersistanceArtifact

class TrainingPipelineConfig:
    def __init__(self, timestamp = datetime.now()):
        timestamp = timestamp.strftime('%d_%m_%Y_%H_%M_%S')
        self.pipeline_name : str = training_pipeline.PIPELINE_NAME
        self.artifact_name : str = training_pipeline.ARTIFACT_NAME
        self.artifact_dir : str = os.path.join(self.artifact_name,timestamp)
        self.timestamp = timestamp

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

class FeatureExtractionConfig:
    def __init__(self, training_pipline_config : TrainingPipelineConfig):
        self.feature_extraction_dir : str = os.path.join(
            training_pipline_config.artifact_dir,
            training_pipeline.FEATURE_EXTRACTION_DIR_NAME
        )
        self.features_data_path : str = os.path.join(
            self.feature_extraction_dir,
            training_pipeline.FEATURE_EXTRACTION_FEATURES_DIR_NAME,
            training_pipeline.FEATURES_DATA_PATH
        )

class DataValidationConfig:
    def __init__(self, training_pipeline_config : TrainingPipelineConfig):
        self.data_validation_dir : str = os.path.join(
            training_pipeline_config.artifact_dir,
            training_pipeline.DATA_VALIDATION_DIR_NAME
        )
        self.validated_data_path : str = os.path.join(
            self.data_validation_dir,
            training_pipeline.DATA_VALIDATION_DATA_DIR_NAME,
            training_pipeline.VALIDATED_DATA_PATH
        )
        self.validation_report_path : str = os.path.join(
            self.data_validation_dir,
            training_pipeline.DATA_VALIDATION_REPORT_DIR_NAME,
            training_pipeline.DATA_VALIDATION_REPORT
        )
        self.data_scheme_path : str = training_pipeline.DATA_SCHEME_PATH

class DataPersistanceConfig:
    def __init__(self, training_pipeline_config : TrainingPipelineConfig):
        self.data_persistance_dir : str = os.path.join(
            training_pipeline_config.artifact_dir,
            training_pipeline.DATA_PERSISTANCE_DIR_NAME
        )
        self.imported_data_path : str = os.path.join(
            self.data_persistance_dir,
            training_pipeline.DATA_PERSISTANCE_DATA_DIR_NAME,
            training_pipeline.IMPORTED_DATA_PATH
        )
        self.database_name = training_pipeline.MONOGDB_DATABASE_NAME
        self.collection_name = training_pipeline.MONGODB_COLLECTION_NAME

class DataEnvelopConfig:
    def __init__(self, feature_extraction_artifact : FeatureExtractionArtifact, data_persistance_artifact : DataPersistanceArtifact, data_validation_artifact : DataValidationArtifact):
        self.feature_extraction_artifact = feature_extraction_artifact
        self.data_persistance_artifact = data_persistance_artifact
        self.data_validation_artifact = data_validation_artifact

class DataTransformationConfig:
    def __init__(self, training_pipeline_config : TrainingPipelineConfig):
        self.data_transformation_dir : str = os.path.join(
            training_pipeline_config.artifact_dir,
            training_pipeline.DATA_TRANSFORMATION_DIR_NAME
        )
        self.train_data_path : str = os.path.join(
            self.data_transformation_dir,
            training_pipeline.DATA_TRANSFORMATION_TRAIN_DIR_NAME,
            training_pipeline.TRAIN_DATA_PATH
        )
        self.test_data_path : str = os.path.join(
            self.data_transformation_dir,
            training_pipeline.DATA_TRANSFORMATION_TEST_DIR_NAME,
            training_pipeline.TEST_DATA_PATH
        )
        self.test_split_ratio : float = training_pipeline.TEST_SPLIT_RATIO

class ModelTrainerConfig:
    def __init__(self, training_pipeline_config : TrainingPipelineConfig):
        self.model_trainer_dir : str = os.path.join(
            training_pipeline_config.artifact_dir,
            training_pipeline.MODEL_TRAINER_DIR_NAME
        )
        self.data_prob_path : str = os.path.join(
            self.model_trainer_dir,
            training_pipeline.MODEL_TRAINER_PROB_DIR_NAME,
            training_pipeline.PROBABILITY_DATA_PATH
        )
        self.artifact_name : str = training_pipeline_config.timestamp + '__' + training_pipeline_config.artifact_name
        self.registered_model_name : str = training_pipeline.REGISTERED_MODEL_NAME

class ModelEvaluationConfig:
    def __init__(self, training_pipeline_config : TrainingPipelineConfig):
        self.model_evaluation_dir_name : str = os.path.join(
            training_pipeline_config.artifact_dir,
            training_pipeline.MODEL_EVALUATION_DIR_NAME
        )
        self.model_evaluation_report_path : str = os.path.join(
            self.model_evaluation_dir_name,
            training_pipeline.MODEL_EVALUATION_REPORT_DIR_NAME,
            training_pipeline.MODEL_EVALUATION_REPORT_PATH
        )
        self.min_recall : float = training_pipeline.MIN_RECALL
        self.min_threshold : float = training_pipeline.MIN_THRESHOLD