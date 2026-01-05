import sys

from phishingsystem.logging.logger import logging
from phishingsystem.exception.exception import PhishingSystemException

from phishingsystem.entity.artifact_entity import ModelEvaluationArtifact, ModelFinalizerArtifact

import mlflow
from mlflow.client import MlflowClient
import json

class ModelFinalizer:
    def __init__(self, model_evaluation_artifact : ModelEvaluationArtifact):
        self.model_evaluation_artifact = model_evaluation_artifact
        self.client = MlflowClient(tracking_uri = self.model_evaluation_artifact.model_tracking_uri)
    
    def _get_production_model(self, model_name : str):
        try:
            return self.client.get_model_version_by_alias(
                name=model_name,
                alias='production'
            )
        except Exception:
            return None
    
    def _load_metrics_from_run(self, run_id : str) -> dict:
        run = self.client.get_run(run_id)
        metrics = dict(run.data.metrics)

        return metrics
    
    def _is_new_model_better(self, new_metrics : dict, prod_metrics : dict, recall_drop : float = 0.02) -> bool:
        if new_metrics['recall'] < prod_metrics['recall'] - recall_drop:
            return False
        return True
    
    def initiate_model_finalization(self) -> ModelFinalizerArtifact:
        try:
            logging.info('Initiating Model Finalization')

            model_name = self.model_evaluation_artifact.registered_model_name
            new_threshold = self.model_evaluation_artifact.threshold

            new_model = mlflow.sklearn.load_model(self.model_evaluation_artifact.model_uri)

            with open(self.model_evaluation_artifact.evaluation_report_path,'r') as file:
                new_metrics = json.load(file)
            
            prod_model = self._get_production_model(model_name)

            if prod_model is None:
                decision = 'PROMOTE_FIRST_TIME'
                logging.info('No production model found. First-time production')
            else:
                prod_metrics = self._load_metrics_from_run(prod_model.run_id)
                decision = 'PROMOTE' if self._is_new_model_better(new_metrics,prod_metrics) else 'REJECT'
            
            with mlflow.start_run(run_name='model_finalization') as run:
                mlflow.log_param('threshold',new_threshold)

                for k,v in new_metrics.items():
                    mlflow.log_metric(k,v)
                
                mlflow.sklearn.log_model(
                    sk_model=new_model,
                    name='final_model',
                    registered_model_name=model_name
                )
                new_run_id = run.info.run_id
            
            versions = self.client.search_model_versions(f"name='{model_name}'")
            new_version = max(versions, key=lambda v: int(v.version)).version

            if decision in ['PROMOTE_FIRST_TIME','PROMOTE']:
                if prod_model is not None:
                    self.client.set_model_version_tag(
                        name=model_name,
                        version=prod_model.version,
                        key='lifecycle',
                        value='archived'
                    )

                self.client.set_registered_model_alias(
                    name=model_name,
                    alias='production',
                    version=new_version
                )
                final_stage='production'
            
            else:
                self.client.set_model_version_tag(
                    name=model_name,
                    version=new_version,
                    key='lifecycle',
                    value='archived'
                )
                final_stage='archived'
            
            logging.info(f'Model Finalization completed. Final Stage: {final_stage}')

            model_finalizer_artifact = ModelFinalizerArtifact(
                model_name=model_name,
                model_version=new_version,
                stage=final_stage,
                threshold=new_threshold,
                run_id=new_run_id
            )
            return model_finalizer_artifact

        except Exception as e:
            raise PhishingSystemException(e,sys)