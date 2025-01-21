import os
import sys

from networksecurity.logging.logger import logging
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.entity.artifact_entity import ClassificationMetricArtifact

from sklearn.metrics import f1_score,precision_score,recall_score

def get_classification_score(y_true,y_pred) -> ClassificationMetricArtifact:
    try:
        model_f1_score = f1_score(y_pred=y_pred,y_true=y_true)
        model_precision_score = precision_score(y_pred=y_pred,y_true=y_true)
        model_recall_score = recall_score(y_pred=y_pred,y_true=y_true)

        classification_metric = ClassificationMetricArtifact(
            f1_score=model_f1_score,
            precision_score=model_precision_score,
            recall_score=model_recall_score
        )

        return classification_metric
    
    except Exception as e:
        raise NetworkSecurityException(e,sys)