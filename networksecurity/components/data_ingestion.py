import pymongo.mongo_client
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

# configuration of the Data Ingestion Config
from networksecurity.entity.config_entity import DataIngestionConfig
from networksecurity.entity.artifact_entity import DataIngestionArtifact

import os
import sys
import numpy as np
import pandas as pd
import pymongo
from typing import List
from sklearn.model_selection import train_test_split

from dotenv import load_dotenv
load_dotenv()

mongo_db_url = os.getenv('MONGO_DB_URL')

class DataIngestion:
    def __init__(self,data_ingestion_config:DataIngestionConfig):
        try:
            self.data_ingestion_config = data_ingestion_config

        except Exception as e:
            raise NetworkSecurityException(e,sys)
    
    def export_collection_as_dataframe(self):
        try:
            database_name = self.data_ingestion_config.database_name
            collection_name = self.data_ingestion_config.collection_name
            self.mongo_client = pymongo.MongoClient(mongo_db_url)
            collection = self.mongo_client[database_name][collection_name]

            df = pd.DataFrame(list(collection.find()))

            if "_id" in df.columns.to_list():
                df.drop(columns='_id',inplace=True)
            
            df.replace({'na':np.nan},inplace=True)

            return df

        except Exception as e:
            raise NetworkSecurityException(e,sys)

    def export_data_to_feature_store(self,dataframe:pd.DataFrame):
        try:
            feature_store_file_path = self.data_ingestion_config.feature_store_file_path

            dir_path = os.path.dirname(feature_store_file_path)
            os.makedirs(dir_path,exist_ok=True)
            dataframe.to_csv(feature_store_file_path,index=False,header=True)

            return dataframe

        except Exception as e:
            raise NetworkSecurityException(e,sys)

    def split_data_as_train_test(self,dataframe:pd.DataFrame):
        try:
            train_set,test_set = train_test_split(
                dataframe,test_size=self.data_ingestion_config.train_test_ratio,random_state=6
            )
            logging.info('Performed train test split on the dataframe')
            logging.info('Exited split_data_as_train_test method of DataIngestion class')

            dir_path = os.path.dirname(self.data_ingestion_config.training_file_path)

            os.makedirs(dir_path,exist_ok=True)

            logging.info('Exporting train and test file path.')

            train_set.to_csv(self.data_ingestion_config.training_file_path,index=False,header=True)

            test_set.to_csv(self.data_ingestion_config.testing_file_path,index=False,header=True)

            logging.info('Exported train and test file path')

        except Exception as e:
            raise NetworkSecurityException(e,sys)

    def initiate_data_ingestion(self):
        try:
            data = self.export_collection_as_dataframe()
            dataframe = self.export_data_to_feature_store(data)
            self.split_data_as_train_test(dataframe)

            data_ingestion_artifact = DataIngestionArtifact(trained_file_path=self.data_ingestion_config.training_file_path,test_file_path=self.data_ingestion_config.testing_file_path)

            return data_ingestion_artifact

        except Exception as e:
            raise NetworkSecurityException(e,sys)
    
