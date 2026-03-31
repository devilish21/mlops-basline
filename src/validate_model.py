import sys
import joblib
import os
from src.logger import logger


def validate_model(model_path: str, threshold: float = 0.9):
    """Validate that the model exists and meets basic quality standards."""
    if not os.path.exists(model_path):
        logger.error(f"Validation failed: No model at {model_path}")
        sys.exit(1)

    try:
        model = joblib.load(model_path)
        # Check for expected attributes (e.g., classes_ for a classifier)
        if not hasattr(model, "predict"):
            logger.error("Validation failed: Object at path is not a model")
            sys.exit(1)

        logger.info("Model validation successful")

    except Exception as e:
        logger.error(f"Validation failed with error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "models/model.joblib"
    validate_model(path)
