import os

PIPELINE_NAME : str = 'URLPhishingDetectionSystem'
ARTIFACT_NAME : str = 'Artifacts'

# Data Preparation
DATA_PREPARATION_DIR_NAME = 'data_preparation'
DATA_PREPARATION_PROCESSED_DIR_NAME = 'processed'
RAW_DATA_PATH = os.path.join('phishingdata','raw_data.csv')
PROCESSED_DATA_PATH = 'processed_data.parquet'
ORIGINAL_URL_COLUMN_NAME = 'url'
PROCESSED_URL_COLUMN_NAME = 'processed_url'
TARGET_COLUMN_NAME = 'label'

# Feature Extraction
FEATURE_EXTRACTION_DIR_NAME = 'feature_extraction'
FEATURE_EXTRACTION_FEATURES_DIR_NAME = 'features'
FEATURES_DATA_PATH = 'features_data.parquet'

# Data Validation
DATA_VALIDATION_DIR_NAME = 'data_validation'
DATA_VALIDATION_DATA_DIR_NAME = 'validated_data'
DATA_VALIDATION_REPORT_DIR_NAME = 'validation_report'
VALIDATED_DATA_PATH = 'validated_data.parquet'
DATA_SCHEME_PATH = os.path.join('data_schema','schema.yaml')
DATA_VALIDATION_REPORT = 'report.json'
PSI_THRESHOLD = 0.25
CHI_SQUARE_THRESHOLD = 0.05
MAX_WARN_FEATURES = 5
MAX_FAIL_FEATURES = 10

# Data Persistance
DATA_PERSISTANCE_DIR_NAME = 'data_persistance'
DATA_PERSISTANCE_DATA_DIR_NAME = 'imported'
IMPORTED_DATA_PATH = 'imported_data.parquet'
DATA_PERSISTANCE_WEIGHTS_DIR_NAME = 'weights'
WEIGHTS_DATA_PATH = 'weights.npy'
MONOGDB_DATABASE_NAME = 'URLPhishingSystem'
MONGODB_FEATURES_COLLECTION_NAME = 'URLStructuralFeatures'
LAST_N_DAYS_FEEDBACK_DATA = 90

# Data Transformation
DATA_TRANSFORMATION_DIR_NAME = 'data_transformation'
DATA_TRANSFORMATION_TRAIN_DIR_NAME = 'train'
TRAIN_DATA_PATH = 'train_arr.npy'
DATA_TRANSFORMATION_TEST_DIR_NAME = 'test'
TEST_DATA_PATH = 'test_arr.npy'
DATA_TRANSFORMATION_WEIGHTS_DIR_NAME = 'weights'
TRAIN_DATA_WEIGHTS_PATH = 'train_data_weights.npy'
TEST_SPLIT_RATIO = 0.2

# Model Trainer
MODEL_TRAINER_DIR_NAME = 'model_training'
MODEL_TRAINER_PROB_DIR_NAME = 'probs'
PROBABILITY_DATA_PATH = 'prob_arr.npy'
REGISTERED_MODEL_NAME = 'phishingDetectionModel'
SHAP_PLOT_DIR_NAME = 'shap_graph'
SHAP_PLOT_PATH = 'shap_graph.png'
IMBALANCE_RATIO_THRESHOLD = 0.2
MAX_CLASS_WEIGHT = 10.0
EXPERIMENT_NAME = 'phishing_detection'

# Model Evaluation
MODEL_EVALUATION_DIR_NAME = 'model_evaluation'
MODEL_EVALUATION_REPORT_DIR_NAME = 'eval_report'
MODEL_EVALUATION_REPORT_PATH = 'report.json'
MIN_THRESHOLD = 0.45
MIN_RECALL = 0.9700

# Model Finalizer
METADATA_PATH = 'metadata/production_model.json'

# Feedback
MONOGODB_FEEDBACK_URL_FEATURES_COLLECTION_NAME = 'FeedbackURLs'