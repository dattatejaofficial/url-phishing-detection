import os
import sys
from dotenv import load_dotenv
load_dotenv()

from phishingsystem.logging.logger import logging
from phishingsystem.exception.exception import PhishingSystemException

import pandas as pd
import pymongo
import hashlib
import json

from phishingsystem.entity.config_entity import DataPersistanceConfig, DataEnvelopConfig
from phishingsystem.entity.artifact_entity import DataPersistanceArtifact, DataEnvelopArtifact

from phishingsystem.utils.main_utils import read_csv_file

MONGODB_URI = os.getenv('MONGODB_URI')
if not MONGODB_URI:
    raise Exception("MONGODB_URI is not set in environement")

class DataPersistance:
    def __init__(self, data_envelop_config : DataEnvelopConfig, data_persistance_config : DataPersistanceConfig):
        self.data_validation_artifact = data_envelop_config.data_validation_artifact
        self.data_persistance_config = data_persistance_config
    
    def _get_collection(self):
        client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=60000)
        db = client[self.data_persistance_config.database_name]
        collection = db[self.data_persistance_config.collection_name]
        return client, collection
    
    def _compute_hash(self, df : pd.DataFrame) -> pd.Series:
        feature_cols = sorted(df.columns)
        normalized = df[feature_cols].copy().round(6).astype(str)
        normalized = normalized.drop_duplicates(ignore_index=True)

        return normalized.agg('|'.join,axis=1).map(lambda x: hashlib.sha256(x.encode()).hexdigest())
    
    def export_data_to_collections(self, df: pd.DataFrame):
        try:
            client, collection = self._get_collection()

            df['feature_hash'] = self._compute_hash(df)
            collection.create_index(
                [('feature_hash', pymongo.ASCENDING)],
                unique = True
            )

            documents = df.to_dict(orient='records')

            operations = []
            for doc in documents:
                operations.append(
                    pymongo.UpdateOne(
                        {'feature_hash' : doc['feature_hash']},
                        {'$setOnInsert' : doc},
                        upsert=True
                    )
                )
            
            batch_size = 2000
            for i in range(0,len(operations),batch_size):
                collection.bulk_write(
                    operations[i:i+batch_size],
                    ordered=False
                )
            logging.info('Exported data to MongoDB Database')

        except Exception as e:
            raise PhishingSystemException(e, sys)

        finally:
            if client:
                client.close()
    
    def import_data_from_collection(self):
        try:
            client, collection = self._get_collection()
            
            documents = list(collection.find())
            df = pd.DataFrame(documents)
            if "_id" in df:
                df.drop(columns="_id",inplace=True)
            
            logging.info('Imported data from MonogDB Database')
            return df
        
        except Exception as e:
            raise PhishingSystemException(e,sys)
        
        finally:
            if client:
                client.close()
    
    def initiate_data_persistance(self):
        try:
            logging.info('Starting Data Persistance')
            if self.data_validation_artifact:       # Data Validation -> Data Persistance
                validated_data_path = self.data_validation_artifact.validated_data_path
                if self.data_validation_artifact.validation_status == "PASS":
                    df = read_csv_file(validated_data_path)
                    self.export_data_to_collections(df)

                    data_persistance_artifact = DataPersistanceArtifact(
                        imported_data_path = None,
                        validated_data_path = validated_data_path
                    )

                else:
                    raise PhishingSystemException("Training stopped to due to Validation failure", sys)
            
            else:       # Data Persistance -> Data Validation
                df = self.import_data_from_collection()
                
                imported_data_path = self.data_persistance_config.imported_data_path
                imported_data_dir = os.path.dirname(imported_data_path)
                os.makedirs(imported_data_dir,exist_ok=True)

                df.to_csv(imported_data_path,header=True,index=False)

                data_persistance_artifact = DataPersistanceArtifact(
                    imported_data_path = imported_data_path,
                    validated_data_path = None
                )
            
            data_envelop_artifact = DataEnvelopArtifact(
                data_validation_artifact = self.data_validation_artifact,
                data_persistance_artifact = data_persistance_artifact
            )

            logging.info('Completed Data Persistance')
            return data_envelop_artifact
        
        except Exception as e:
            raise PhishingSystemException(e,sys)