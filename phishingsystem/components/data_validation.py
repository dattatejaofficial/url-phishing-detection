import os
import sys

from phishingsystem.logging.logger import logging
from phishingsystem.exception.exception import PhishingSystemException
from phishingsystem.utils.main_utils import read_yaml_file, read_csv_file

import json
import pandas as pd

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
    
    def initiate_data_validation(self):
        try:
            logging.info('Initiating Data Validation')
            if not self.data_persistance_artifact:     # Data Validation -> Data Persistance
                df = read_csv_file(self.feature_extraction_artifact.features_data_path)
            else:
                df = read_csv_file(self.data_persistance_artifact.imported_data_path)       # Data Persistance -> Data Validation
            
            self._validate_data(df)
            if self.report['errors']:
                self.report['status'] = "FAIL"

            report_path = self.data_validation_config.validation_report_path
            report_dir = os.path.dirname(report_path)
            os.makedirs(report_dir, exist_ok=True)

            with open(report_path,'w') as file:
                json.dump(self.report,file,indent=4)
            
            validated_data_path = None
            if self.report['status'] == "PASS":
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