import os
import sys

from phishingsystem.logging.logger import logging
from phishingsystem.exception.exception import PhishingSystemException

from phishingsystem.entity.config_entity import ModelTrainerConfig
from phishingsystem.entity.artifact_entity import DataTransformationArtifact, ModelTrainerArtifact

from phishingsystem.utils.main_utils import save_numpy_array, load_numpy_array, evaluate_model

import numpy as np
from sklearn.model_selection import StratifiedKFold
from xgboost import XGBClassifier
from sklearn.metrics import recall_score
from hyperopt import hp, tpe, STATUS_OK, Trials, fmin
import mlflow
from mlflow.models import infer_signature

class ModelTrainer:
    def __init__(self, data_transformation_artifact : DataTransformationArtifact, model_trainer_config : ModelTrainerConfig):
        self.data_transformation_artifact = data_transformation_artifact
        self.model_trainer_config = model_trainer_config

    def _train_model(self, train_data, test_data):
        try:
            X_train, y_train = train_data[:,:-1], train_data[:,-1].astype(int)
            X_test, y_test = test_data[:,:-1], test_data[:,-1].astype(int)

            search_space = {
                "max_depth" : hp.quniform("max_depth",3,10,1),
                "learning_rate" : hp.loguniform("learning_rate",np.log(0.01),np.log(0.2)),
                "n_estimators" : hp.quniform("n_estimators",100,600,50),
                "subsample" : hp.uniform("subsample",0.6,1.0),
                "colsample_bytree" : hp.uniform("colsample_bytree",0.6,1.0),
                "gamma" : hp.uniform("gamma",0,5),
                "min_child_weight" : hp.qloguniform("min_child_weight",1,10,1),
                "reg_alpha" : hp.loguniform("reg_alpha",np.log(1e-3),np.log(1)),
                "reg_lambda" : hp.loguniform("reg_lambda",np.log(1),np.log(10))
            }

            def objective(params : dict):
                params['max_depth'] = int(params['max_depth'])
                params['n_estimators'] = int(params['n_estimators'])
                params['min_child_weight'] = int(params['min_child_weight'])

                params.update({
                    "objective" : "binary:logistic",
                    "eval_metric" : "logloss",
                    "random_state" : 42,
                    "tree_method" : "hist",
                    "n_jobs" : -1
                })

                skf = StratifiedKFold(n_splits=5,shuffle=True,random_state=42)
                recalls = []

                for tr_idx, val_idx in skf.split(X_train, y_train):
                    X_tr, y_tr = X_train[tr_idx], y_train[tr_idx]
                    X_val, y_val = X_train[val_idx], y_train[val_idx]

                    model = XGBClassifier(**params)
                    model.fit(X_tr,y_tr)

                    preds = model.predict(X_val)
                    recalls.append(recall_score(y_val,preds))
                
                mean_recall = np.mean(recalls)

                with mlflow.start_run(nested=True):
                    mlflow.log_params(params)
                    mlflow.log_metric('cv_mean_recall',mean_recall)
                
                return {'loss' : -mean_recall, 'status' : STATUS_OK}

            trials = Trials()

            with mlflow.start_run(run_name='hyperopt_search'):
                best_params = fmin(
                    algo = tpe.suggest,
                    trials = trials,
                    fn = objective,
                    space = search_space,
                    max_evals = 50
                )

                best_params['max_depth'] = int(best_params['max_depth'])
                best_params['n_estimators'] = int(best_params['n_estimators'])
                best_params['min_child_weight'] = int(best_params['min_child_weight'])

                best_params.update({
                    'objective' : 'binary:logistic',
                    'eval_metric' : 'logloss',
                    'random_state' : 42,
                    'n_jobs' : -1
                })

                final_model = XGBClassifier(**best_params)
                final_model.fit(X_train,y_train)

                train_preds = final_model.predict(X_train)
                test_preds = final_model.predict(X_test)
                test_probs = final_model.predict_proba(X_test)

                train_metrics = evaluate_model(y_train, train_preds)
                test_metrics = evaluate_model(y_test, test_preds)

                mlflow.log_params(best_params)

                for k,v in train_metrics.items():
                    mlflow.log_metric(f'train_{k}',v)
                
                for k,v in test_metrics.items():
                    mlflow.log_metric(f'test_{k}',v)
                
                signature = infer_signature(X_train, final_model.predict(X_train))

                model_info = mlflow.sklearn.log_model(
                    sk_model=final_model,
                    artifact_path=self.model_trainer_config.artifact_name,
                    registered_model_name=self.model_trainer_config.registered_model_name,
                    signature=signature
                )

            model_version = model_info.registered_model_version
            registered_name = self.model_trainer_config.registered_model_name
            model_uri = f'models:/{registered_name}/{model_version}'
            tracking_uri = mlflow.get_tracking_uri()
            return test_probs, model_uri, model_version, tracking_uri, registered_name
        
        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def initiate_model_trainer(self):
        try:
            logging.info('Initiating Model Training')
            train_arr = load_numpy_array(self.data_transformation_artifact.train_data_path)
            test_arr = load_numpy_array(self.data_transformation_artifact.test_data_path)

            test_probs, model_uri, model_version, tracking_uri, reg_model_name = self._train_model(train_arr, test_arr)
            logging.info('Loaded MlFlow Artifacts')

            test_prob_arr_path = self.model_trainer_config.data_prob_path
            test_prob_arr_dir = os.path.dirname(test_prob_arr_path)
            os.makedirs(test_prob_arr_dir,exist_ok=True)

            save_numpy_array(test_probs, test_prob_arr_path)

            model_trainer_artifact = ModelTrainerArtifact(
                model_uri = model_uri,
                registered_model_name = reg_model_name,
                model_version = model_version,
                model_tracking_uri = tracking_uri,
                test_data_probs_path = test_prob_arr_path
            )
            logging.info('Completed Model Training')
            return model_trainer_artifact

        except Exception as e:
            raise PhishingSystemException(e,sys)