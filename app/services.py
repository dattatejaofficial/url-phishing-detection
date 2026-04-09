import os
from dotenv import load_dotenv
load_dotenv()

import threading

from azure.storage.blob import BlobServiceClient

import pymongo
import hashlib
from datetime import datetime, timezone

import pickle
import json
import pandas as pd

from app.utils.url_cleaner import URLCleaner
from app.utils.url_feature_extraction import URLFeaturesExtraction

AZURE_ARTIFACT_STORAGE_CONNECTION_STRING = os.getenv('AZURE_ARTIFACT_STORAGE_CONNECTION_STRING')
if AZURE_ARTIFACT_STORAGE_CONNECTION_STRING is None:
    raise Exception('AZURE_ARTIFACT_STORAGE_CONNECTION_STRING is not set in the environment')

AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER = os.getenv('AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER')
if AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER is None:
    raise Exception('AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER is not set in the environment')

MONGODB_URI = os.getenv('MONGODB_URI')
if MONGODB_URI is None:
    raise Exception('MONGODB_URI is not set in the environment')

MONOGDB_DATABASE_NAME = 'URLPhishingSystem'
MONOGODB_FEEDBACK_URL_FEATURES_COLLECTION_NAME = 'FeedbackURLs'
METADATA_PATH = 'metadata/production_model.json'

class ModelService:
    def __init__(self):
        self.model = None
        self.current_model_path = None
        self.lock = threading.Lock()
        self.blob_service = BlobServiceClient.from_connection_string(AZURE_ARTIFACT_STORAGE_CONNECTION_STRING)
        self.container = self.blob_service.get_container_client(AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER)
    
    def _get_model_path(self):
        blob = self.container.get_blob_client(METADATA_PATH)
        data = json.loads(blob.download_blob().readall())

        return data['model_path']
    
    def _download_model(self, path):
        blob = self.blob_service.get_blob_client(container = AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER, blob = path)
        
        return pickle.loads(blob.download_blob().readall())
    
    def load_model(self):
        model_path = self._get_model_path()

        with self.lock:
            if model_path == self.current_model_path:
                return None
            
            model = self._download_model(model_path)
            self.model = model
            self.current_model_path = model_path
        
        return model
    
    async def auto_reload(self, interval=60):
        if self.model is None:
            self.load_model()
        
        return self.model
    
    def predict(self, df: pd.DataFrame):
        with self.lock:
            if self.model is None:
                raise Exception('Model not loaded')
            
            return self.model.predict(None, df)

class FeatureService:
    def extract(self, url: str):
        cleaned_url = URLCleaner(url).initiate_cleaning_url()
        
        features = URLFeaturesExtraction(cleaned_url).extract_features()
        features.pop("url",None)

        return cleaned_url, features

class FeedbackService:
    def __init__(self):
        self.client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=60000, maxPoolSize = 50)
        db = self.client[MONOGDB_DATABASE_NAME]
        self.collection = db[MONOGODB_FEEDBACK_URL_FEATURES_COLLECTION_NAME]
    
    def store(self, url, user_label, model_prediction : None, model_confidence : None):
        feature_service = FeatureService()
        
        cleaned_url, features = feature_service.extract(url)
        url_hash = hashlib.sha256(cleaned_url.encode()).hexdigest()

        features.update({
            'label' : user_label,
            'created_at' : datetime.now(timezone.utc),
            'model_prediction' : model_prediction,
            'model_confidence' : model_confidence
        })

        self.collection.update_one(
            {'url_hash' : url_hash},
            {"$set" : features},
            upsert=True
        )