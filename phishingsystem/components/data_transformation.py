import os
import sys

from phishingsystem.logging.logger import logging
from phishingsystem.exception.exception import PhishingSystemException

from phishingsystem.entity.config_entity import DataTransformationConfig
from phishingsystem.entity.artifact_entity import DataEnvelopArtifact, DataTransformationArtifact

from phishingsystem.utils.main_utils import read_csv_file, save_numpy_array

from sklearn.model_selection import train_test_split

class DataTransformation:
    def __init__(self, data_envelop_artifact : DataEnvelopArtifact, data_transformation_config : DataTransformationConfig):
        if not data_envelop_artifact.data_validation_artifact:      # Data Validation -> Data Persistance
            self.data_validation_artifact = data_envelop_artifact.data_persistance_artifact
        else:       # Data Persistance -> Data Validation
            self.data_validation_artifact = data_envelop_artifact.data_validation_artifact

        self.data_transformation_config = data_transformation_config

    def initiate_data_transformation(self) -> DataTransformationArtifact:
        try:
            if self.data_validation_artifact.validated_data_path:
                logging.info('Initiating Data Transformation')
                
                df = read_csv_file(self.data_validation_artifact.validated_data_path)
                train_arr, test_arr = train_test_split(df.values, test_size=self.data_transformation_config.test_split_ratio, random_state=42)
                logging.info('Split the data into train & test arrays')

                train_arr_path = self.data_transformation_config.train_data_path
                train_arr_dir = os.path.dirname(train_arr_path)
                os.makedirs(train_arr_dir,exist_ok=True)

                test_arr_path = self.data_transformation_config.test_data_path
                test_arr_dir = os.path.dirname(test_arr_path)
                os.makedirs(test_arr_dir,exist_ok=True)

                save_numpy_array(train_arr,train_arr_path)
                save_numpy_array(test_arr,test_arr_path)
                logging.info('Saved the train array and test array')

                data_transformation_artifact = DataTransformationArtifact(
                    train_data_path = train_arr_path,
                    test_data_path = test_arr_path
                )

                logging.info('Completed Data Transformation')
                return data_transformation_artifact
            
            else:
                raise ValueError("Validated data path is missing")

        except Exception as e:
            raise PhishingSystemException(e,sys)