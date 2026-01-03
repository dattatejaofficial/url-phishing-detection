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