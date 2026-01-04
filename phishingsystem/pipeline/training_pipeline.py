import sys
from phishingsystem.exception.exception import PhishingSystemException

from phishingsystem.entity.config_entity import (
    TrainingPipelineConfig,
    DataPreparationConfig,
    FeatureExtractionConfig,
    DataValidationConfig,
    DataPersistanceConfig,
    DataEnvelopConfig
)

from phishingsystem.entity.artifact_entity import (
    DataPreparationArtifact,
    FeatureExtractionArtifact,
    DataValidationArtifact
)

from phishingsystem.components.data_preparation import DataPreparation
from phishingsystem.components.feature_extraction import FeatureExtraction
from phishingsystem.components.data_validation import DataValidation
from phishingsystem.components.data_persistance import DataPersistance

import time

class TrainingPipeline:
    def __init__(self):
        self.training_pipeline_config = TrainingPipelineConfig()
    
    def start_data_preparation(self) -> DataPreparationArtifact:
        try:
            data_preparation_config = DataPreparationConfig(training_pipeline_config = self.training_pipeline_config)
            data_preparation = DataPreparation(data_preparation_config = data_preparation_config)
            data_preparation_artifact = data_preparation.initiate_data_preparation()
            return data_preparation_artifact

        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def start_feature_extraction(self, data_preparation_artifact : DataPreparationArtifact) -> FeatureExtractionArtifact:
        try:
            feature_extraction_config = FeatureExtractionConfig(training_pipline_config = self.training_pipeline_config)
            feature_extraction = FeatureExtraction(data_preparation_artifact = data_preparation_artifact, feature_extraction_config = feature_extraction_config)
            feature_extraction_artifact = feature_extraction.initiate_feature_extraction()
            return feature_extraction_artifact

        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def start_data_validation(self, feature_extraction_artifact : FeatureExtractionArtifact) -> DataValidationArtifact:
        try:
            data_validation_config = DataValidationConfig(training_pipeline_config = self.training_pipeline_config)
            data_envelop_config = DataEnvelopConfig(feature_extraction_artifact=feature_extraction_artifact, data_persistance_artifact=None, data_validation_artifact=None)
            data_validation = DataValidation(data_envelop_config=data_envelop_config, data_validation_config=data_validation_config)
            data_validation_artifact = data_validation.initiate_data_validation()
            return data_validation_artifact.data_validation_artifact
        
        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def start_data_persistance(self, data_validation_artifact : DataValidationArtifact):
        try:
            data_persistance_config = DataPersistanceConfig(training_pipeline_config = self.training_pipeline_config)
            data_envelop_config = DataEnvelopConfig(feature_extraction_artifact=None, data_persistance_artifact=data_persistance_config,data_validation_artifact=data_validation_artifact)
            data_persistance = DataPersistance(data_envelop_config=data_envelop_config, data_persistance_config=data_persistance_config)
            data_persistance_artifact = data_persistance.initiate_data_persistance()
            return data_persistance_artifact.data_persistance_artifact

        except Exception as e:
            raise PhishingSystemException(e,sys)
        
    def run_pipeline(self) -> None:
        try:
            data_preparation_artifact = self.start_data_preparation()
            feature_extraction_artifact = self.start_feature_extraction(data_preparation_artifact)
            data_validation_artifact = self.start_data_validation(feature_extraction_artifact)
            data_persistance_artifact = self.start_data_persistance(data_validation_artifact)

        except Exception as e:
            raise PhishingSystemException(e,sys)

if __name__ == '__main__':
    pipeline = TrainingPipeline()
    pipeline.run_pipeline()
    print('Completed Pipeline')