import sys
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.components.data_ingestion import DataIngestion
from networksecurity.components.data_validation import DataValidation
from networksecurity.components.data_transformation import DataTransformation
from networksecurity.entity.config_entity import TrainingPipelineConfig
from networksecurity.entity.config_entity import DataIngestionConfig,DataValidationConfig,DataTransformationConfig

if __name__ == '__main__':
    try:
        training_pipeline_config = TrainingPipelineConfig()
        data_ingestion_config = DataIngestionConfig(training_pipeline_config=training_pipeline_config)
        data_ingestion = DataIngestion(data_ingestion_config=data_ingestion_config)

        logging.info('Initiate Data Ingestion Config')
        data_ingestion_artifact = data_ingestion.initiate_data_ingestion()
        logging.info('Data Inititiation completed')
        
        data_validation_config = DataValidationConfig(training_pipeline_config)
        data_validation = DataValidation(data_ingestion_artifact,data_validation_config)

        logging.info('Initiate Data Validation Config')
        data_validation_artifact = data_validation.initiate_data_validation()
        logging.info('Data Validation Initiated')

        data_transformation_config = DataTransformationConfig(training_pipeline_config)
        data_transformation = DataTransformation(data_validation_artifact,data_transformation_config)

        logging.info('Inititate Data Transformation Config')
        data_transformation_artifact = data_transformation.initiate_data_transformation()
        logging.info('Data Transformation Initiated')

        print(data_transformation_artifact)

    except Exception as e:
        raise NetworkSecurityException(e,sys)
    
