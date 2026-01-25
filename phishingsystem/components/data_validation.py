import os
import sys

from phishingsystem.logging.logger import logging
from phishingsystem.exception.exception import PhishingSystemException
from phishingsystem.utils.main_utils import read_yaml_file, read_csv_file

import json
import pandas as pd
from datetime import datetime, timedelta

from evidently.legacy.report import Report
from evidently.legacy.metrics import ColumnDriftMetric

from phishingsystem.entity.config_entity import DataValidationConfig, DataEnvelopConfig
from phishingsystem.entity.artifact_entity import DataValidationArtifact, DataEnvelopArtifact

class DataValidation:
    def __init__(self, data_envelop_config : DataEnvelopConfig, data_validation_config : DataValidationConfig):
        self.feature_extraction_artifact = data_envelop_config.feature_extraction_artifact
        self.data_persistance_artifact = data_envelop_config.data_persistance_artifact
        self.data_validation_config = data_validation_config
    
        self.schema = read_yaml_file(self.data_validation_config.data_scheme_path)
        self.report = {
            "status" : "PASS",
            "errors" : {},
            "warnings" : {}
        }
    
    def _validate_schema(self, df: pd.DataFrame):
        expected_columns = set(self.schema['columns'].keys())
        actual_columns = set(df.columns)

        missing_columns = expected_columns - actual_columns
        extra_columns = actual_columns - expected_columns

        if missing_columns:
            self.report['errors']['missing_columns'] = list(missing_columns)
        
        if extra_columns:
            self.report['warnings']['extra_columns'] = list(extra_columns)
        
        logging.info('Validated Schema of the Features Dataset')
    
    def _validate_dtypes(self, df: pd.DataFrame):
        try:
            dtype_errors = {}
            for col, rules in self.schema['columns'].items():
                if col not in df.columns:
                    continue

                expected_dtype = rules.get('dtype')
                actual_dtype = str(df[col].dtype)

                if actual_dtype != expected_dtype:
                    dtype_errors[col] = {
                        'expected' : expected_dtype,
                        'actual' : actual_dtype
                    }
            
            if dtype_errors:
                self.report['errors']['dtype_mismatch'] = dtype_errors
            
            logging.info('Validated data type of the features')

        except Exception as e:
            raise PhishingSystemException(e, sys)
    
    def _validate_allowed_values(self, df: pd.DataFrame):
        try:
            value_errors = {}
            for col, rules in self.schema['columns'].items():
                if col not in df.columns:
                    continue

                allowed = rules.get('allowed_values')
                if not allowed:
                    continue

                invalid_values = set(df[col]) - set(allowed)
                if invalid_values:
                    value_errors[col] = list(invalid_values)
            
            if value_errors:
                self.report['errors']['invalid_values'] = value_errors
            
            logging.info('Validated allowed values in the features dataset')

        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def _validate_data(self, df: pd.DataFrame):
        self._validate_schema(df)
        if 'missing_columns' in self.report['errors']:
            return
        
        self._validate_dtypes(df)
        if 'dtype_mismatch' in self.report['errors']:
            return
        
        self._validate_allowed_values(df)
    
    def _detect_data_drift(self, reference_df: pd.DataFrame, current_df: pd.DataFrame):
        try:
            numerical_columns = list(self.schema.get('numerical_columns'))
            categorical_columns = list(self.schema.get('categorical_columns'))
            metrics = []
            
            for feature in numerical_columns:
                metrics.append(ColumnDriftMetric(column_name=feature,stattest='psi',stattest_threshold=self.data_validation_config.psi_threshold))
            
            for feature in categorical_columns:
                metrics.append(ColumnDriftMetric(column_name=feature,stattest='chi_square',stattest_threshold=self.data_validation_config.chi_square_threshold))

            report = Report(metrics=metrics)
            report.run(reference_data=reference_df, current_data=current_df)
            report_dict = report.as_dict()

            numerical_drift = {}
            categorical_drift = {}
            drifted_features = []

            for metric in report_dict['metrics']:
                result = metric['result']
                feature = result['column_name']
                drift_detected = result['drift_detected']

                if feature in numerical_columns:
                    psi_value = result['drift_score']
                    numerical_drift[feature] = psi_value

                    if psi_value is not None and drift_detected:
                        drifted_features.append(feature)

                elif feature in categorical_columns:
                    chi_square_value = result['drift_score']
                    categorical_drift[feature] = chi_square_value

                    if drift_detected:
                        drifted_features.append(feature)
            
            if len(drifted_features) >= self.data_validation_config.max_warn_features:
                status = 'WARN'
            elif len(drifted_features) >= self.data_validation_config.max_fail_features:
                status = 'FAIL'
            else:
                status = 'PASS'
            
            self.report['data_drift'] = {
                'status' : status,
                'drifted_features' : list(set(drifted_features)),
                'numerical_drift' : numerical_drift,
                'categorical_drift' : categorical_drift
            }

            if status == 'WARN':
                self.report['warnings']['data_drift'] = f'Drift detected in {len(drifted_features)} features'
            elif status == 'FAIL':
                self.report['errors']['data_drift'] = f'Severe drift detected in {len(drifted_features)} features'
            
            logging.info('Completed Drift detection')

        except Exception as e:
            raise PhishingSystemException(e,sys)
              
    def initiate_data_validation(self):
        try:
            logging.info('Initiating Data Validation')
            if not self.data_persistance_artifact:     # Data Validation -> Data Persistance
                df = read_csv_file(self.feature_extraction_artifact.features_data_path)
                self._validate_data(df)
            else:
                df = read_csv_file(self.data_persistance_artifact.imported_data_path)       # Data Persistance -> Data Validation
                self._validate_data(df)

                if not self.report['errors']:
                    end_time = df.index.max()
                    start_time = end_time - timedelta(days = 7)

                    reference_df = df.loc[df.index < start_time]
                    current_df = df.loc[(df.index >= start_time) & (df.index <= end_time)]

                    self._detect_data_drift(reference_df=reference_df, current_df=current_df)
            
            if self.report['errors']:
                self.report['status'] = "FAIL"

            report_path = self.data_validation_config.validation_report_path
            report_dir = os.path.dirname(report_path)
            os.makedirs(report_dir, exist_ok=True)

            with open(report_path,'w') as file:
                json.dump(self.report,file,indent=4)
            
            validated_data_path = None
            if self.report['status'] != "FAIL":
                validated_data_path = self.data_validation_config.validated_data_path
                validated_dir = os.path.dirname(validated_data_path)
                os.makedirs(validated_dir,exist_ok=True)

                df.to_csv(validated_data_path, index=False, header=True)
                logging.info('Saved the Validated data')
            
            data_validation_artifact = DataValidationArtifact(
                validated_data_path = validated_data_path,
                validation_report_path = report_path,
                validation_status = self.report["status"]
            )

            data_envelop_artifact = DataEnvelopArtifact(
                data_validation_artifact = data_validation_artifact,
                data_persistance_artifact = self.data_persistance_artifact
            )

            logging.info('Completed Data Validation')
            return data_envelop_artifact

        except Exception as e:
            raise PhishingSystemException(e, sys)