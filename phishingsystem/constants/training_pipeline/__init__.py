import os

PIPELINE_NAME : str = 'URLPhishingDetectionSystem'
ARTIFACT_NAME : str = 'Artifacts'

# Data Preparation
DATA_PREPARATION_DIR_NAME = 'data_preparation'
DATA_PREPARATION_PROCESSED_DIR_NAME = 'processed'
RAW_DATA_PATH = os.path.join('phishingdata','raw_data.csv')
PROCESSED_DATA_PATH = 'processed_data.csv'
ORIGINAL_URL_COLUMN_NAME = 'url'
PROCESSED_URL_COLUMN_NAME = 'processed_url'
TARGET_COLUMN_NAME = 'label'

# Feature Extraction
FEATURE_EXTRACTION_DIR_NAME = 'feature_extraction'
FEATURE_EXTRACTION_FEATURES_DIR_NAME = 'features'
FEATURES_DATA_PATH = 'features_data.csv'

# Data Validation
DATA_VALIDATION_DIR_NAME = 'data_validation'
DATA_VALIDATION_DATA_DIR_NAME = 'validated_data'
DATA_VALIDATION_REPORT_DIR_NAME = 'validation_report'
VALIDATED_DATA_PATH = 'validated_data.csv'
DATA_SCHEME_PATH = os.path.join('data_schema','schema.yaml')
DATA_VALIDATION_REPORT = 'report.json'

# Data Persistance
DATA_PERSISTANCE_DIR_NAME = 'data_persistance'
DATA_PERSISTANCE_DATA_DIR_NAME = 'imported'
IMPORTED_DATA_PATH = 'imported_data.csv'
MONOGDB_DATABASE_NAME = 'URLPhishingSystem'
MONGODB_FEATURES_COLLECTION_NAME = 'URLStructuralFeatures'

# Data Transformation
DATA_TRANSFORMATION_DIR_NAME = 'data_transformation'
DATA_TRANSFORMATION_TRAIN_DIR_NAME = 'train'
TRAIN_DATA_PATH = 'train_arr.npy'
DATA_TRANSFORMATION_TEST_DIR_NAME = 'test'
TEST_DATA_PATH = 'test_arr.npy'
TEST_SPLIT_RATIO = 0.2

# Model Trainer
MODEL_TRAINER_DIR_NAME = 'model_training'
MODEL_TRAINER_PROB_DIR_NAME = 'probs'
PROBABILITY_DATA_PATH = 'prob_arr.npy'
REGISTERED_MODEL_NAME = 'phishingDetectionModel'
IMBALANCE_RATIO_THRESHOLD = 0.2
MAX_CLASS_WEIGHT = 10.0

# Model Evaluation
MODEL_EVALUATION_DIR_NAME = 'model_evaluation'
MODEL_EVALUATION_REPORT_DIR_NAME = 'eval_report'
MODEL_EVALUATION_REPORT_PATH = 'report.json'
MIN_THRESHOLD = 0.45
MIN_RECALL = 0.9700

# Model Finalizer
MODEL_FINALIZER_DIR_NAME = 'model_finalizer'
MODEL_FINALIZER_THRESHOLD_DIR_NAME = 'report'
FINAL_THRESHOLD_PATH = 'threshold.json'

# Feedback
MONOGODB_URLS_COLLECTION_NAME = 'FeedbackURLs'