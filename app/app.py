import asyncio
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Annotated

import pandas as pd

from app.services import ModelService, FeatureService, FeedbackService

class PredictionRequest(BaseModel):
    url : str

BinaryInt = Annotated[int, Field(ge=0, le=1, strict=True)]

class FeedbackRequest(BaseModel):
    url : str
    prediction : BinaryInt
    user_label : BinaryInt
    confidence : float | None

def create_app():
    model_service = ModelService()
    feature_service = FeatureService()
    feedback_service = FeedbackService()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        model_service.load_model()
        asyncio.create_task(model_service.auto_reload())
        yield
    
    app = FastAPI(lifespan=lifespan)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins = ["*"],
        allow_credentials = True,
        allow_methods = ["POST","GET"],
        allow_headers = ["*"]
    )

    @app.post("/predict")
    async def predict(req: PredictionRequest):
        try:
            def logic():
                _, features = feature_service.extract(req.url)
                df = pd.DataFrame([features])
                return model_service.predict(df)

            result = await run_in_threadpool(logic)
            row = result.iloc[0]

            return {
                "probability" : float(row['probability']),
                'prediction' : bool(int(row['prediction']))
            }
        except Exception as e:
            raise HTTPException(500, str(e))
    
    @app.post('/feedback')
    async def feedback(req: FeedbackRequest):
        try:
            feedback_service.store(req.url, req.user_label, req.prediction, req.confidence)
            return {'status':'stored'}
        except Exception as e:
            raise HTTPException(500, str(e))
    
    return app

app = create_app()

if __name__ == '__main__':
    uvicorn.run("app.app:app",host='0.0.0.0',port=8000, reload=False)