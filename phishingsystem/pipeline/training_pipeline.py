import sys
from phishingsystem.exception.exception import PhishingSystemException

from phishingsystem.entity.config_entity import (
    TrainingPipelineConfig,
    DataPreparationConfig,
    FeatureExtractionConfig
)

from phishingsystem.entity.artifact_entity import (
    DataPreparationArtifact,
    FeatureExtractionArtifact
)

from phishingsystem.components.data_preparation import DataPreparation
from phishingsystem.components.feature_extraction import FeatureExtraction

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

        
    def run_pipeline(self) -> None:
        try:
            data_preparation_artifact = self.start_data_preparation()
            feature_extraction_artifact = self.start_feature_extraction(data_preparation_artifact)

        except Exception as e:
            raise PhishingSystemException(e,sys)

if __name__ == '__main__':
    pipeline = TrainingPipeline()
    pipeline.run_pipeline()
    print('Completed Pipeline')