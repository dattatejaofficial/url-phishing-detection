import os
import sys

from phishingsystem.logging.logger import logging
from phishingsystem.exception.exception import PhishingSystemException

from phishingsystem.entity.config_entity import ModelFinalizerConfig
from phishingsystem.entity.artifact_entity import ModelEvaluationArtifact, ModelFinalizerArtifact

import mlflow
from mlflow.client import MlflowClient
from mlflow.pyfunc.model import PythonModel

from azure.storage.blob import BlobServiceClient

from datetime import datetime, timezone
import pandas as pd
import numpy as np
import json

AZURE_ARTIFACT_STORAGE_CONNECTION_STRING = os.getenv('AZURE_ARTIFACT_STORAGE_CONNECTION_STRING')
if not AZURE_ARTIFACT_STORAGE_CONNECTION_STRING:
    raise Exception('AZURE_ARTIFACT_STORAGE_CONNECTION_STRING is not set in environment')

AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER = os.getenv('AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER')
if not AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER:
    raise Exception('AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER is not set in environment')

class ModelWrapper(PythonModel):
    def __init__(self, model, threshold):
        self.model = model
        self.threshold = threshold
        
    def predict(self, context, model_input : pd.DataFrame) -> dict[str,np.ndarray]:
        proba = self.model.predict_proba(model_input)[:,1]
        preds = (proba >= self.threshold).astype(int)

        return {
            'probability' : proba,
            'prediction' : preds
        }

class ModelFinalizer:
    def __init__(self, model_evaluation_artifact : ModelEvaluationArtifact, model_finalizer_config : ModelFinalizerConfig):
        self.model_evaluation_artifact = model_evaluation_artifact
        self.model_finalizer_config = model_finalizer_config
    
    def _load_production_metadata(self):
        try:
            blob_service = BlobServiceClient.from_connection_string(AZURE_ARTIFACT_STORAGE_CONNECTION_STRING)
            container_client = blob_service.get_container_client(AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER)
            blob_client = container_client.get_blob_client(self.model_finalizer_config.metadata_path)

            if not blob_client.exists():
                return None

            data = blob_client.download_blob().readall().decode('utf-8')
            return json.loads(data)
        
        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def _get_metrics(self, run_id):
        client = MlflowClient()
        run = client.get_run(run_id)

        return run.data.metrics
    
    def _is_new_model_better(self, new_metrics, prod_metrics, recall_drop = 0.02):
        new_recall = new_metrics.get('recall',0)
        prod_recall = prod_metrics.get('eval_recall',0)

        new_f1 = new_metrics.get('f1_score',0)
        prod_f1 = prod_metrics.get('eval_f1_score',0)

        if new_recall < (prod_recall - recall_drop):
            return False

        if new_f1 < prod_f1:
            return False
        
        return True
        
    def _update_production_config(self, model_uri, run_id):
        try:
            blob_service = BlobServiceClient.from_connection_string(AZURE_ARTIFACT_STORAGE_CONNECTION_STRING)
            container_client = blob_service.get_container_client(AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER)

            if not container_client.exists():
                raise Exception('Container does not exists')

            data = {
                'model_uri' : model_uri,
                'run_id' : run_id,
                'updated_at' : datetime.now(timezone.utc).isoformat()
            }

            blob_client = container_client.get_blob_client(self.model_finalizer_config.metadata_path)
            blob_client.upload_blob(json.dumps(data), overwrite=True)
        
        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def initiate_model_finalization(self) -> ModelFinalizerArtifact:
        try:
            logging.info('Initiating Model Finalization')

            with open(self.model_evaluation_artifact.evaluation_report_path,'r') as file:
                new_metrics = json.load(file)

            new_threshold = self.model_evaluation_artifact.threshold
            trainer_run_id = self.model_evaluation_artifact.run_id
            raw_model_uri = f'runs:/{trainer_run_id}/raw_model'
            
            prod_metadata = self._load_production_metadata()

            if prod_metadata is None:
                promote = True
                logging.info('No production model found. First-time production')
            else:
                prod_metrics = self._get_metrics(prod_metadata['run_id'])
                promote = self._is_new_model_better(new_metrics, prod_metrics)
            
            if not promote:
                logging.info('New model rejected. Keeping current production model.')

                return ModelFinalizerArtifact(
                    model_uri=prod_metadata['model_uri'],
                    run_id=prod_metadata['run_id'],
                    stage='rejected',
                    threshold=self.model_evaluation_artifact.threshold
                )
            
            mlflow.end_run()

            with mlflow.start_run(run_name='final_model') as run:
                
                mlflow.set_tag('stage','production')
                mlflow.set_tag('pipeline_step','finalizer')
                mlflow.set_tag('trainer_run_id',trainer_run_id)

                mlflow.log_param('threshold',new_threshold)

                for k,v in new_metrics.items():
                    mlflow.log_metric(f'final_{k}', v)
                
                base_model = mlflow.sklearn.load_model(raw_model_uri)
                wrapped_model = ModelWrapper(base_model, new_threshold)

                mlflow.pyfunc.log_model(
                    name='final_model',
                    python_model=wrapped_model,
                )

                final_uri = f'runs:/{run.info.run_id}/final_model'

                self._update_production_config(model_uri=final_uri,run_id=run.info.run_id)

            logging.info(f"Final decision: {'PROMOTED' if promote else 'REJECTED'}")

            model_finalizer_artifact = ModelFinalizerArtifact(
                model_uri = final_uri,
                run_id = run.info.run_id,
                stage = 'production',
                threshold = new_threshold
            )
            return model_finalizer_artifact

        except Exception as e:
            raise PhishingSystemException(e,sys)