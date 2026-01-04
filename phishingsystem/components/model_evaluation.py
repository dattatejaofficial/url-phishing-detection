import os
import sys
import json

from phishingsystem.logging.logger import logging
from phishingsystem.exception.exception import PhishingSystemException

from phishingsystem.entity.config_entity import ModelEvaluationConfig
from phishingsystem.entity.artifact_entity import ModelTrainerArtifact, ModelEvaluationArtifact

from phishingsystem.utils.main_utils import load_numpy_array

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_recall_curve

class ModelEvaluation:
    def __init__(self, model_trainer_artifact : ModelTrainerArtifact, model_evaluation_config : ModelEvaluationConfig):
        self.model_trainer_artifact = model_trainer_artifact
        self.model_evaluation_config = model_evaluation_config
    
    def _select_best_threshold(self, y_true, y_prob, min_recall : float, min_threshold : float):
        try:
            precision, recall, thresholds = precision_recall_curve(y_true, y_prob)

            precision = precision[:-1]
            recall = recall[:-1]
            thresholds = np.array(thresholds)

            valid_idxs = np.where(
                (recall >= min_recall) & 
                (thresholds >= min_threshold)
            )[0]

            if len(valid_idxs) == 0:
                raise ValueError(f'No threshold satisfies recall >= {min_recall} and threshold >= {min_threshold}')
            
            best_idx = valid_idxs[np.argmax(precision[valid_idxs])]
            best_threshold = thresholds[best_idx]

            return {
                'threshold' : float(best_threshold),
                'accuracy' : float(accuracy_score(y_true, (y_prob >= best_threshold).astype(int))),
                'precision' : float(precision[best_idx]),
                'recall' : float(recall[best_idx]),
                'f1_score' : float(f1_score(y_true, (y_prob >= best_threshold).astype(int)))
            }

        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def initiate_model_evaluation(self):
        try:
            logging.info('Initiating Model Evaluation')
            min_recall = self.model_evaluation_config.min_recall
            min_threshold = self.model_evaluation_config.min_threshold
            report_path = self.model_evaluation_config.model_evaluation_report_path

            test_data = load_numpy_array(self.model_trainer_artifact.test_data_path)
            probs = load_numpy_array(self.model_trainer_artifact.test_data_probs_path)[:,1]
            y = test_data[:,-1].astype(int)

            best_metrics = self._select_best_threshold(y,probs,min_recall,min_threshold)

            report_dir = os.path.dirname(report_path)
            os.makedirs(report_dir,exist_ok=True)

            with open(report_path,'w') as file:
                json.dump(best_metrics, file, indent=4)
            logging.info('Saved the Metrics report')
            
            model_evaluation_artifact = ModelEvaluationArtifact(
                model_uri = self.model_trainer_artifact.model_uri,
                registered_model_name = self.model_trainer_artifact.registered_model_name,
                model_version = self.model_trainer_artifact.model_version,
                model_tracking_uri = self.model_trainer_artifact.model_tracking_uri,
                threshold = best_metrics['threshold']
            )
            logging.info('Completed Model Evaluation')
            return model_evaluation_artifact

        except Exception as e:
            raise PhishingSystemException(e,sys)