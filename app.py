import os
import sys
import tempfile
import shutil
from dotenv import load_dotenv
load_dotenv()

from phishingsystem.exception.exception import PhishingSystemException

import threading
import asyncio
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal

import pymongo
import hashlib
from datetime import datetime, timezone

import mlflow
import mlflow.artifacts
import json
import pandas as pd

from azure.storage.blob import BlobServiceClient

from phishingsystem.utils.url_preparation.url_cleaner import URLCleaner
from phishingsystem.utils.url_preparation.url_feature_extraction import URLFeaturesExtraction
from phishingsystem.constants.training_pipeline import MONOGDB_DATABASE_NAME, MONOGODB_FEEDBACK_URL_FEATURES_COLLECTION_NAME, METADATA_PATH

MONGODB_URI = os.getenv('MONGODB_URI')
if not MONGODB_URI:
    raise Exception("MONGODB_URI is not set in environement")

AZURE_ARTIFACT_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
if not AZURE_ARTIFACT_STORAGE_CONNECTION_STRING:
    raise Exception('AZURE_STORAGE_CONNECTION_STRING is not set in environment')

AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER = os.getenv('AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER')
if not AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER:
    raise Exception('AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER is not set in environment')

CURRENT_MODEL_URI = None
model = None
model_lock = threading.Lock()

mongo_client = None
db = None
collection = None

def fetch_model_uri_from_blob():
    try:
        blob_service = BlobServiceClient.from_connection_string(AZURE_ARTIFACT_STORAGE_CONNECTION_STRING)
        container = blob_service.get_container_client(AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER)
        blob = container.get_blob_client(METADATA_PATH)
        raw = blob.download_blob().readall()
        data = json.loads(raw)

        return data['model_uri']
    except Exception as e:
        raise PhishingSystemException(e,sys)

def load_model_from_blob():
    global CURRENT_MODEL_URI

    model_uri = fetch_model_uri_from_blob()

    if CURRENT_MODEL_URI == model_uri:
        return None
    
    loaded_model = mlflow.pyfunc.load_model(model_uri)

    CURRENT_MODEL_URI = model_uri
    return loaded_model

async def model_reloader():
    global model

    while True:
        try:
            new_model = load_model_from_blob()
            
            if new_model is not None:
                with model_lock:
                    model = new_model
    
        except Exception as e:
            print(f'Model Reload Error {str(e)}')
        
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, mongo_client, db, collection

    mongo_client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=60000)
    db = mongo_client[MONOGDB_DATABASE_NAME]
    collection = db[MONOGODB_FEEDBACK_URL_FEATURES_COLLECTION_NAME]

    initial_model = load_model_from_blob()

    if initial_model is None:
        raise PhishingSystemException('Failed to load model', sys)
    
    with model_lock:
        model = initial_model

    asyncio.create_task(model_reloader())

    yield

    if mongo_client:
        mongo_client.close()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

class PredictionRequest(BaseModel):
    url : str

class FeedbackRequest(BaseModel):
    url : str
    model_prediction : Literal["phishing","legitimate"]
    user_label : Literal["phishing","legitimate"]
    confidence : float | None

@app.post('/predict')
async def predict_route(request : PredictionRequest):
    try:
        def blocking_logic():
            cleaner = URLCleaner(request.url)
            cleaned_url = cleaner.initiate_cleaning_url()

            extractor = URLFeaturesExtraction(cleaned_url)
            features = extractor.extract_features()
            features = {k: v for k,v in features.items() if k != 'url'}
            df = pd.DataFrame([features])

            return model.predict(df)
            
        result = await run_in_threadpool(blocking_logic)

        return {
            'probability' : float(result['probability'][0]),
            'prediction' : bool(result['prediction'])
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/feedback')
async def feedback_route(request : FeedbackRequest):
    feedback_doc = {
        "url" : request.url,
        "model_prediction" : request.model_prediction,
        "user_label" : request.user_label,
        "confidence" : request.confidence,
    }

    cleaner = URLCleaner(feedback_doc['url'])
    cleaned_url = cleaner.initiate_cleaning_url()

    extractor = URLFeaturesExtraction(cleaned_url)
    features = extractor.extract_features()

    url_hash = hashlib.sha256(cleaned_url.encode()).hexdigest()

    features['label'] = feedback_doc['user_label']
    features['created_at'] = datetime.now(timezone.utc) 
    collection.update_one(
        {'url_hash' : url_hash},
        {"$set" : features},
        upsert=True
    )

    return {'status' : 'feedback stored'}

if __name__ == '__main__':
    uvicorn.run(app=app,host='0.0.0.0',port=8000)