import os
from dotenv import load_dotenv
load_dotenv()

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
from mlflow import MlflowClient
import pandas as pd

from phishingsystem.utils.url_preparation.url_cleaner import URLCleaner
from phishingsystem.utils.url_preparation.url_feature_extraction import URLFeaturesExtraction
from phishingsystem.constants.training_pipeline import REGISTERED_MODEL_NAME, MONOGDB_DATABASE_NAME, MONOGODB_FEEDBACK_URL_FEATURES_COLLECTION_NAME

MONGODB_URI = os.getenv('MONGODB_URI')
if not MONGODB_URI:
    raise Exception("MONGODB_URI is not set in environement")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

model_name = REGISTERED_MODEL_NAME
client = MlflowClient()
model = mlflow.pyfunc.load_model(f"models:/{model_name}@production")

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

    client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=60000)
    db = client[MONOGDB_DATABASE_NAME]
    collection = db[MONOGODB_FEEDBACK_URL_FEATURES_COLLECTION_NAME]

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