import sys
from phishingsystem.exception.exception import PhishingSystemException
from phishingsystem.logging.logger import logging

from phishingsystem.entity.config_entity import (
    TrainingPipelineConfig,
    DataPersistanceConfig,
    DataValidationConfig,
    DataEnvelopConfig,
    DataTransformationConfig,
    ModelTrainerConfig,
    ModelEvaluationConfig,
    ModelFinalizerConfig
)

from phishingsystem.entity.artifact_entity import (
    DataPersistanceArtifact,
    DataValidationArtifact,
    DataEnvelopArtifact,
    DataTransformationArtifact,
    ModelTrainerArtifact,
    ModelEvaluationArtifact,
    ModelFinalizerArtifact
)

from phishingsystem.components.data_persistance import DataPersistance
from phishingsystem.components.data_validation import DataValidation
from phishingsystem.components.data_transformation import DataTransformation
from phishingsystem.components.model_training import ModelTrainer
from phishingsystem.components.model_evaluation import ModelEvaluation
from phishingsystem.components.model_finalizer import ModelFinalizer

class RetrainingPipeline:
    def __init__(self):
        self.retraining_pipeline_config = TrainingPipelineConfig()
    
    def start_data_persistance(self) -> DataPersistanceArtifact:
        try:
            data_persistance_config = DataPersistanceConfig(training_pipeline_config=self.retraining_pipeline_config)
            data_envelop_config = DataEnvelopConfig(data_persistance_artifact=data_persistance_config, feature_extraction_artifact=None, data_validation_artifact=None)
            data_persistance = DataPersistance(data_envelop_config=data_envelop_config, data_persistance_config=data_persistance_config)
            data_persistance_artifact = data_persistance.initiate_data_persistance()
            return data_persistance_artifact.data_persistance_artifact
        
        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def start_data_validation(self, data_persistance_artifact : DataPersistanceArtifact) -> DataValidationArtifact:
        try:
            data_validation_config = DataValidationConfig(training_pipeline_config = self.retraining_pipeline_config)
            data_envelop_config = DataEnvelopConfig(feature_extraction_artifact=None, data_persistance_artifact=data_persistance_artifact, data_validation_artifact=None)
            data_validation = DataValidation(data_envelop_config=data_envelop_config, data_validation_config=data_validation_config)
            data_validation_artifact = data_validation.initiate_data_validation()
            return data_validation_artifact.data_validation_artifact

        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def start_data_transformation(self, data_validation_artifact : DataValidationArtifact) -> DataTransformationArtifact:
        try:
            data_transformation_config = DataTransformationConfig(training_pipeline_config = self.retraining_pipeline_config)
            data_envelop_artifact = DataEnvelopArtifact(data_validation_artifact=data_validation_artifact,data_persistance_artifact=None)
            data_transformation = DataTransformation(data_envelop_artifact=data_envelop_artifact,data_transformation_config=data_transformation_config)
            data_transformation_artifact = data_transformation.initiate_data_transformation()
            return data_transformation_artifact

        except Exception as e:
            raise PhishingSystemException(e,sys)

    def start_model_training(self, data_transformation_artifact : DataTransformationArtifact) -> ModelTrainerArtifact:
        try:
            model_trainer_config = ModelTrainerConfig(training_pipeline_config = self.retraining_pipeline_config)
            model_training = ModelTrainer(data_transformation_artifact = data_transformation_artifact, model_trainer_config = model_trainer_config)
            model_training_artifact = model_training.initiate_model_trainer()
            return model_training_artifact

        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def start_model_evaluation(self, model_trainer_artifact : ModelTrainerArtifact) -> ModelEvaluationArtifact:
        try:
            model_evaluation_config = ModelEvaluationConfig(training_pipeline_config = self.training_pipeline_config)
            model_evaluation = ModelEvaluation(model_trainer_artifact = model_trainer_artifact, model_evaluation_config = model_evaluation_config)
            model_evaluation_artifact = model_evaluation.initiate_model_evaluation()
            return model_evaluation_artifact

        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def start_model_finalization(self, model_evaluation_artifact : ModelEvaluationArtifact) -> ModelFinalizerArtifact:
        try:
            model_finalizer_config = ModelFinalizerConfig(training_pipeline_config = self.training_pipeline_config)
            model_finalizer = ModelFinalizer(model_evaluation_artifact = model_evaluation_artifact, model_finalizer_config = model_finalizer_config)
            model_finalizer_artifact = model_finalizer.initiate_model_finalization()
            return model_finalizer_artifact

        except Exception as e:
            raise PhishingSystemException(e,sys)

    def run_pipeline(self):
        try:
            logging.info('Initiating Retraining Pipeline')
            data_persistance_artifact = self.start_data_persistance()
            data_validation_artifact = self.start_data_validation(data_persistance_artifact)
            data_transformation_artifact = self.start_data_transformation(data_validation_artifact)
            model_trainer_artifact = self.start_model_training(data_transformation_artifact)
            model_evaluation_artifact = self.start_model_evaluation(model_trainer_artifact)
            self.start_model_finalization(model_evaluation_artifact)
            logging.info("Completed Retraining Pipeline")

        except Exception as e:
            raise PhishingSystemException(e,sys)

if __name__ == '__main__':
    pipeline = RetrainingPipeline()
    pipeline.run_pipeline()