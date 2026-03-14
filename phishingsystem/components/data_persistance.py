import os
import sys
from dotenv import load_dotenv
load_dotenv()

from phishingsystem.logging.logger import logging
from phishingsystem.exception.exception import PhishingSystemException

import pandas as pd
import pymongo
from pymongo.errors import BulkWriteError
import hashlib
from datetime import datetime, timezone
from phishingsystem.entity.config_entity import DataPersistanceConfig, DataEnvelopConfig
from phishingsystem.entity.artifact_entity import DataPersistanceArtifact, DataEnvelopArtifact

from phishingsystem.utils.main_utils import read_parquet_file, compute_sample_weights, save_numpy_array

MONGODB_URI = os.getenv('MONGODB_URI')
if not MONGODB_URI:
    raise Exception("MONGODB_URI is not set in environement")

class DataPersistance:
    def __init__(self, data_envelop_config : DataEnvelopConfig, data_persistance_config : DataPersistanceConfig):
        self.data_validation_artifact = data_envelop_config.data_validation_artifact
        self.data_persistance_config = data_persistance_config
    
    def _get_collection(self, collection_name):
        client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=60000)
        db = client[self.data_persistance_config.database_name]
        collection = db[collection_name]
        return client, collection
    
    def _compute_hash(self, url : pd.DataFrame) -> pd.Series:
        return hashlib.sha256(url.encode()).hexdigest()
    
    def export_data_to_collections(self, df: pd.DataFrame):
        try:
            client, collection = self._get_collection(self.data_persistance_config.raw_features_collection_name)

            operations = []

            for _, row in df.iterrows():
                url = row.get(self.data_persistance_config.url_column_name,"")
                url_hash = self._compute_hash(url)

                doc = row.to_dict()
                doc.pop(self.data_persistance_config.url_column_name, None)

                doc["_id"] = url_hash
                doc['timestamp'] = datetime.now(timezone.utc)

                operations.append(
                    pymongo.UpdateOne(
                        {"_id" : url_hash},
                        {"$setOnInsert" : doc},
                        upsert=True
                    )
                )

            batch_size = 2000

            for i in range(0, len(operations), batch_size):
                batch = operations[i:i+batch_size]

                try:
                    collection.bulk_write(
                        batch,
                        ordered=False
                    )
                except BulkWriteError as bwe:
                    for err in bwe.details.get("writeErrors", []):
                        if err['code'] != 11000:
                            raise

            logging.info('Exported data to MongoDB Database')

        except Exception as e:
            raise PhishingSystemException(e, sys)

        finally:
            if client:
                client.close()
    
    def import_data_from_collection(self, collection_name):
        try:
            client, collection = self._get_collection(collection_name)
            
            documents = list(collection.find())

            if not documents:
                return pd.DataFrame()
            
            df = pd.DataFrame(documents)
            df['timestamp'] = pd.to_datetime(df['timestamp'],utc=True)
            df = df.drop_duplicates(ignore_index=True)
            
            logging.info('Imported data from MonogDB Database')
            return df
        
        except Exception as e:
            raise PhishingSystemException(e,sys)
        
        finally:
            if client:
                client.close()
    
    def merge_data(self, df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        try:
            df = pd.concat([df1, df2[df1.columns]], ignore_index=True)
            df = df.sort_values(by='timestamp', ascending=False, ignore_index=True)
            df = df.drop_duplicates(subset='_id',keep='last')

            return df

        except Exception as e:
            raise PhishingSystemException(e,sys)
    
    def initiate_data_persistance(self):
        try:
            logging.info('Starting Data Persistance')
            if self.data_validation_artifact:       # Data Validation -> Data Persistance
                validated_data_path = self.data_validation_artifact.validated_data_path
                if self.data_validation_artifact.validation_status == "PASS":
                    df = read_parquet_file(validated_data_path)
                    self.export_data_to_collections(df)
                    logging.info("Exported data into the Database")

                    df = df.drop(columns=[self.data_persistance_config.url_column_name])
                    df.to_parquet(validated_data_path, index=False, engine='pyarrow')

                    data_persistance_artifact = DataPersistanceArtifact(
                        imported_data_path = None,
                        validated_data_path = validated_data_path,
                        weights_data_path = None
                    )

                else:
                    raise PhishingSystemException("Training stopped to due to Validation failure", sys)
            
            else:       # Data Persistance -> Data Validation
                raw_data_df = self.import_data_from_collection(self.data_persistance_config.raw_features_collection_name)
                other_data_df = self.import_data_from_collection(self.data_persistance_config.feedback_features_collection_name)
                
                if other_data_df.empty:
                    logging.info("The feedback data is empty")
                    df = raw_data_df
                    df = df.sort_values(by='timestamp',ascending=False,ignore_index=True)
                else:
                    df = self.merge_data(raw_data_df, other_data_df)
                    logging.info("Merged the Existing dataset & the Feedback dataset")

                weights = compute_sample_weights(df, self.data_persistance_config.last_n_days_feedback_data)
                logging.info("Computed weights")

                df.drop(columns=['timestamp','_id'],inplace=True)
                df[self.data_persistance_config.target_column_name] = df.pop(self.data_persistance_config.target_column_name)

                weights_data_path = self.data_persistance_config.weights_data_path
                weights_data_dir = os.path.dirname(weights_data_path)
                os.makedirs(weights_data_dir,exist_ok=True)

                imported_data_path = self.data_persistance_config.imported_data_path
                imported_data_dir = os.path.dirname(imported_data_path)
                os.makedirs(imported_data_dir,exist_ok=True)

                df.to_parquet(imported_data_path,index=False, engine='pyarrow')
                logging.info("Saved the merged dataset")

                save_numpy_array(weights, weights_data_path)
                logging.info("Saved the weights")

                data_persistance_artifact = DataPersistanceArtifact(
                    imported_data_path = imported_data_path,
                    validated_data_path = None,
                    weights_data_path = weights_data_path
                )
            
            data_envelop_artifact = DataEnvelopArtifact(
                data_validation_artifact = self.data_validation_artifact,
                data_persistance_artifact = data_persistance_artifact
            )

            logging.info('Completed Data Persistance')
            return data_envelop_artifact
        
        except Exception as e:
            raise PhishingSystemException(e,sys)