from fastapi.testclient import TestClient
from app import app
import os
import pytest

client = TestClient(app)
API_KEY = "enterprise-secret-key"
HEADERS = {"X-API-Key": API_KEY}

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()

def test_predict_unauthorized():
    response = client.post("/predict", json={
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2
    })
    assert response.status_code == 403

def test_predict_with_key():
    # Note: Requires model to be present at models/model.joblib
    if not os.path.exists('models/model.joblib'):
        pytest.skip("Model not found, skipping prediction test")
        
    response = client.post("/predict", headers=HEADERS, json={
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2
    })
    assert response.status_code == 200
    assert "prediction" in response.json()
    assert "model_version" in response.json()
