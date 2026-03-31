from pydantic import BaseModel, Field
from typing import List

class IrisFeatures(BaseModel):
    sepal_length: float = Field(..., gt=0, description="Length of the sepal in cm")
    sepal_width: float = Field(..., gt=0, description="Width of the sepal in cm")
    petal_length: float = Field(..., gt=0, description="Length of the petal in cm")
    petal_width: float = Field(..., gt=0, description="Width of the petal in cm")

class PredictionResponse(BaseModel):
    prediction: int
    model_version: str
    status: str = "success"

class TrainingConfig(BaseModel):
    n_estimators: int = Field(default=100, ge=10)
    max_depth: int = Field(default=5, ge=1)
