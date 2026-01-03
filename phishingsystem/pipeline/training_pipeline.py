import sys
from phishingsystem.exception.exception import PhishingSystemException

from phishingsystem.entity.config_entity import (
    TrainingPipelineConfig,
    DataPreparationConfig
)

from phishingsystem.entity.artifact_entity import (
    DataPreparationArtifact
)

from phishingsystem.components.data_preparation import DataPreparation

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
        
    def run_pipeline(self) -> None:
        try:
            data_preparation_artifact = self.start_data_preparation()

        except Exception as e:
            raise PhishingSystemException(e,sys)

if __name__ == '__main__':
    pipeline = TrainingPipeline()
    
    now = time.time()
    pipeline.run_pipeline()

    print('Completed Pipline')

    print('\n')

    print(time.time() - now)