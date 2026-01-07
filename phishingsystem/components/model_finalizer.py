import os
import tempfile
import sys

from phishingsystem.logging.logger import logging
from phishingsystem.exception.exception import PhishingSystemException

from phishingsystem.entity.config_entity import ModelFinalizerConfig
from phishingsystem.entity.artifact_entity import ModelEvaluationArtifact, ModelFinalizerArtifact

import mlflow
from mlflow.client import MlflowClient
from mlflow.pyfunc.model import PythonModel
from mlflow.artifacts import download_artifacts
from joblib import load
import pandas as pd
import numpy as np
import json

class ModelWrapper(PythonModel):
    def __init__(self):
        self.model = None
        self.threshold = None
    
    def load_context(self, context):
        self.model = load(context.artifacts['model_path'])

        with open(context.artifacts['threshold_path'],'r') as file:
            self.threshold = json.load(file)['threshold']
    
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
        if new_metrics.get('recall',0.0) < prod_metrics.get('recall',0.0) - recall_drop:
            return False
        return True
    
    def initiate_model_finalization(self) -> ModelFinalizerArtifact:
        try:
            logging.info('Initiating Model Finalization')

            model_name = self.model_evaluation_artifact.registered_model_name
            new_threshold = self.model_evaluation_artifact.threshold
            print(new_threshold)

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

                report_path = self.model_finalizer_config.model_finalizer_report_path
                report_dir = os.path.dirname(report_path)
                os.makedirs(report_dir,exist_ok=True)

                with open(report_path,'w') as file:
                    json.dump({'threshold' : new_threshold}, file, indent = 4)

                for k,v in new_metrics.items():
                    if k != 'threshold':
                        mlflow.log_metric(k,v)

                local_model_dir = download_artifacts(self.model_evaluation_artifact.model_uri)
                print("Local Model Directory: ", local_model_dir)

                model_file_path = os.path.join(local_model_dir,'model.pkl')
                print("Model file path: ", model_file_path)

                mlflow.pyfunc.log_model(
                    name='final_model',
                    python_model=ModelWrapper(),
                    artifacts={
                        'model_path' : model_file_path,
                        'threshold_path' : report_path
                        },
                    registered_model_name=model_name,
                    model_config={'threshold' : new_threshold}
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
                run_id=new_run_id,
                report_path = report_path
            )
            return model_finalizer_artifact

        except Exception as e:
            raise PhishingSystemException(e,sys)