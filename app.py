from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
import joblib
import numpy as np
import os
import mlflow
from src.schemas import IrisFeatures, PredictionResponse
from src.logger import logger

# Production configurations
API_KEY = os.getenv("API_KEY", "enterprise-secret-key")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

app = FastAPI(title="Elite Iris MLOps API", version="1.0.0")

# MLflow Tracking Configuration
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://172.19.0.2:5000")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment("Elite-Iris-Experiment")


@mlflow.trace(name="load_model_artifact")
def load_cached_model(path: str):
    return joblib.load(path)


# Model Loading

MODEL_PATH = 'models/model.joblib'


async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    raise HTTPException(
        status_code=403, detail="Could not validate credentials"
    )


@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": os.path.exists(MODEL_PATH)}


@mlflow.trace(name="inference_request")
@app.post("/predict", response_model=PredictionResponse)
def predict(features: IrisFeatures, api_key: str = Depends(get_api_key)):
    if not os.path.exists(MODEL_PATH):
        logger.error("Model prediction failed: Model not found")
        raise HTTPException(status_code=500, detail="Model artifact missing")

    try:
        model = load_cached_model(MODEL_PATH)
        data = np.array([[
            features.sepal_length,
            features.sepal_width,
            features.petal_length,
            features.petal_width
        ]])
        prediction = model.predict(data)

        logger.info(
            "Prediction successful", extra={"prediction": int(prediction[0])}
        )

        return PredictionResponse(
            prediction=int(prediction[0]),
            model_version="v1.0.0"
        )
    except Exception as e:
        logger.error("Prediction failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Internal inference error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
