import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

import mlflow
from mlflow import MlflowClient
import pandas as pd

from phishingsystem.utils.url_preparation.url_cleaner import URLCleaner
from phishingsystem.utils.url_preparation.url_feature_extraction import URLFeaturesExtraction
from phishingsystem.constants.training_pipeline import REGISTERED_MODEL_NAME

app = FastAPI()

model_name = REGISTERED_MODEL_NAME
client = MlflowClient()
model = mlflow.pyfunc.load_model(f"models:/{model_name}@production")

class PredictionRequest(BaseModel):
    url : str

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

if __name__ == '__main__':
    uvicorn.run(app=app,host='127.0.0.1',port=8000)