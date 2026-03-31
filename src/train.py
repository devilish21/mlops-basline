import os
import joblib
import pandas as pd
import mlflow
import mlflow.sklearn
import mlflow.system_metrics
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score
)
import hydra
from omegaconf import DictConfig
from src.logger import logger
from src.schemas import TrainingConfig


@mlflow.trace(name="data_loading")
def load_data(path: str):
    return pd.read_csv(path)


@mlflow.trace
@hydra.main(config_path="../config", config_name="config", version_base="1.2")
def train_model(cfg: DictConfig):
    """Enterprise-grade training with MLflow 3.x patterns."""
    logger.info("Starting Elite training pipeline", extra={"config": cfg})

    # Validate training config
    train_cfg = TrainingConfig(**cfg.model.params)

    try:
        # Load data
        df = load_data(cfg.data.raw_path)

        # MLflow Tracking
        mlflow.set_tracking_uri(cfg.mlflow.tracking_uri)
        mlflow.set_experiment(cfg.mlflow.experiment_name)

        # Enable system metrics with high-frequency sampling (for short runs)
        mlflow.set_system_metrics_sampling_interval(1)

        with mlflow.start_run(log_system_metrics=True):
            # 1. New MLflow 3.x Dataset Tracking
            train_dataset = mlflow.data.from_pandas(df, name="iris_dataset")
            X = train_dataset.df.drop('target', axis=1)
            y = train_dataset.df['target']

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=cfg.data.test_size,
                random_state=cfg.model.params.random_state
            )

            # 2. Train Model
            clf = RandomForestClassifier(
                n_estimators=train_cfg.n_estimators,
                max_depth=train_cfg.max_depth,
                random_state=cfg.model.params.random_state
            )
            clf.fit(X_train, y_train)

            # 3. Enhanced log_model (Linking to LoggedModel entity)
            model_info = mlflow.sklearn.log_model(
                sk_model=clf,
                name=cfg.mlflow.registered_model_name,
                params=cfg.model.params,
                input_example=X_train.head(3),
                registered_model_name=cfg.mlflow.registered_model_name
            )

            # 4. Evaluation & Logging
            logged_model = mlflow.get_logged_model(model_info.model_id)
            y_pred = clf.predict(X_test)
            # Calculate metrics
            metrics = {
                "accuracy": accuracy_score(y_test, y_pred),
                "precision": precision_score(
                    y_test, y_pred, average='weighted'
                ),
                "recall": recall_score(
                    y_test, y_pred, average='weighted'
                ),
                "f1": f1_score(
                    y_test, y_pred, average='weighted'
                )
            }

            # Log to standard "Metrics" tab
            mlflow.log_metrics(metrics)

            # Log to "Model metrics" tab (Linked to LoggedModel)
            mlflow.log_metrics(
                metrics=metrics,
                model_id=logged_model.model_id,
                dataset=train_dataset
            )

            # Save local artifact for local testing
            model_path = os.path.join(
                cfg.paths.model_dir, cfg.paths.model_name
            )
            os.makedirs(cfg.paths.model_dir, exist_ok=True)
            joblib.dump(clf, model_path)

            # 5. Traditional Artifact Logging (for the Artifacts tab)
            mlflow.log_artifact(model_path)

            logger.info(
                "Elite Training successful",
                extra={
                    "accuracy": metrics["accuracy"],
                    "model_id": logged_model.model_id,
                    "model_path": model_path
                }
            )

    except Exception as e:
        logger.error("Training failed", extra={"error": str(e)})
        raise e


if __name__ == "__main__":
    train_model()
