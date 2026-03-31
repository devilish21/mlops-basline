import os
import joblib
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import hydra
from omegaconf import DictConfig
from src.logger import logger
from src.schemas import TrainingConfig


@hydra.main(config_path="../config", config_name="config", version_base="1.2")
def train_model(cfg: DictConfig):
    """Enterprise-grade training with Hydra and MLflow."""
    logger.info("Starting training pipeline", extra={"config": cfg})

    # Validate training config
    train_cfg = TrainingConfig(**cfg.model.params)

    try:
        # Load data
        df = pd.read_csv(cfg.data.raw_path)
        X = df.drop('target', axis=1)
        y = df['target']

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=cfg.data.test_size,
            random_state=cfg.model.params.random_state
        )

        # MLflow Tracking
        mlflow.set_tracking_uri(cfg.mlflow.tracking_uri)
        mlflow.set_experiment(cfg.mlflow.experiment_name)

        with mlflow.start_run():
            clf = RandomForestClassifier(
                n_estimators=train_cfg.n_estimators,
                max_depth=train_cfg.max_depth,
                random_state=cfg.model.params.random_state
            )
            clf.fit(X_train, y_train)

            y_pred = clf.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

            # Log params and metrics
            mlflow.log_params(cfg.model.params)
            mlflow.log_metric("accuracy", accuracy)

            # Register model
            mlflow.sklearn.log_model(
                clf,
                "iris_model",
                registered_model_name=cfg.mlflow.registered_model_name
            )

            # Save local artifact
            model_path = os.path.join(
                cfg.paths.model_dir, cfg.paths.model_name
            )
            os.makedirs(cfg.paths.model_dir, exist_ok=True)
            joblib.dump(clf, model_path)

            logger.info(
                "Training successful",
                extra={"accuracy": accuracy, "model_path": model_path}
            )

    except Exception as e:
        logger.error("Training failed", extra={"error": str(e)})
        raise e


if __name__ == "__main__":
    train_model()
