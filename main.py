import sys
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.components.data_ingestion import DataIngestion
from networksecurity.entity.config_entity import DataIngestionConfig,TrainingPipelineConfig

if __name__ == '__main__':
    try:
        training_pipeline_config = TrainingPipelineConfig()
        data_ingestion_config = DataIngestionConfig(training_pipeline_config=training_pipeline_config)
        data_ingestion = DataIngestion(data_ingestion_config=data_ingestion_config)

        logging.info('Initiate Data Ingestion Config')

        data_ingestion_artifact = data_ingestion.initiate_data_ingestion()

        print(data_ingestion_artifact)

    except Exception as e:
        raise NetworkSecurityException(e,sys)