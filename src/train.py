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



@hydra.main(config_path="../config", config_name="config", version_base="1.2")
def train_model(cfg: DictConfig):
    # MLflow Tracking
    mlflow.set_tracking_uri(cfg.mlflow.tracking_uri)
    mlflow.set_experiment(cfg.mlflow.experiment_name)
    
    with mlflow.tracing.trace(name="Elite-Training-Flow"):
        # Validate training config
        train_cfg = TrainingConfig(**cfg.model.params)

        try:
            # Load data
            df = load_data(cfg.data.raw_path)

            # 3.x Robust setup
            mlflow.sklearn.autolog(log_models=True, log_datasets=True)
            mlflow.set_system_metrics_sampling_interval(1)

            with mlflow.start_run(log_system_metrics=True) as run:
                logger.info(f"MLflow Run ID: {run.info.run_id}")
                logger.info(f"Tracking URI: {mlflow.get_tracking_uri()}")
                
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

                # 3. Explicit log_model with artifact_path (for UI visibility)
                mlflow.sklearn.log_model(
                    sk_model=clf,
                    artifact_path="model",
                    registered_model_name=cfg.mlflow.registered_model_name
                )

                # 4. Evaluation & Logging
                logged_model_id = run.info.run_id # Simplified for 3.x autolog
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

                # Log to standard "Metrics" tab (Autolog handles these, so we skip manual to avoid IntegrityError)
                # mlflow.log_metrics(metrics)

                # Save local artifact
                model_path = os.path.join(
                    cfg.paths.model_dir, cfg.paths.model_name
                )
                os.makedirs(cfg.paths.model_dir, exist_ok=True)
                joblib.dump(clf, model_path)

                # Explicitly log the folder
                mlflow.log_artifacts(cfg.paths.model_dir, artifact_path="model_output")

                logger.info(
                    "Elite Training successful",
                    extra={
                        "accuracy": metrics["accuracy"],
                        "model_id": logged_model_id,
                        "model_path": model_path
                    }
                )

        except Exception as e:
            logger.error("Training failed", extra={"error": str(e)})
            raise e


if __name__ == "__main__":
    train_model()
