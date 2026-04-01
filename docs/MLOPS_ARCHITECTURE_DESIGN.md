# 🏛️ Elite-Iris MLOps Pipeline: Architecture and System Design Document

## 1. Executive Summary

- **Overview**: The Elite-Iris MLOps Pipeline is an end-to-end, automated machine learning platform designed to seamlessly transition models from experimentation into production. Built with a focus on reproducibility, scalability, and observability, the system orchestrates data validation, model training, and API deployment.
- **Business Value**: Reduces the time-to-market for ML models from weeks to minutes by automating the CI/CD lifecycle, minimizing manual intervention, and enforcing strict data and model quality checks.
- **Key Capabilities**:

  - Automated Data Validation (Great Expectations)
  - Cryptographic Data Versioning (DVC + MinIO S3)
  - Full-Fledged Experiment Tracking & Model Registry (MLflow)
  - Separated CI and CD Pipelines (Jenkins) for focused testing, building, and delivery
  - Image and Configuration Artifact Repository (Nexus)
  - Secured, Containerized Inference API deployed via OpenShift and Helm
- **Success Metrics**: 
  - 100% reproducible training runs.
  - Zero downtime API deployments.
  - <50ms inference latency constraint.

## 2. System Overview

The Elite-Iris MLOps architecture embraces a "Producer-Consumer" relationship between data generation, model training, and model serving. 
- **End-to-end Workflow**: Data Scientists/Engineers (Producers) modify datasets tracked via DVC. A push to Bitbucket triggers the Jenkins CI Pipeline via SCM Polling. The CI pipeline validates data, trains the model, tracks metrics in MLflow, builds a Docker image, and explicitly pushes the Docker image and Helm charts to the Nexus Repository. Subsequently, the Jenkins CD Pipeline pulls the Helm charts from Nexus and triggers OpenShift. OpenShift then fetches the Docker image directly from Nexus and executes the deployment.
- **Key Components**:
  - **Data Layer**: DVC paired with an S3-compatible MinIO backend.
  - **Logic & Training Layer**: Scikit-Learn pipelines structured with Hydra configuration management.
  - **Tracking Layer**: MLflow for parameter, metric, system hardware tracking, and model registry.
  - **Artifact Repository Layer**: Nexus Repository Manager for storing Docker images and Helm charts.
  - **Deployment Layer**: OpenShift executing FastAPI pods for real-time inference, orchestrated via Helm and backed by **CephFS** for model persistence.
  - **Orchestration Layer**: Jenkins executing multi-stage autonomous CI and CD workflows.

## 3. Architecture Diagram 
*(Please refer to the separate [MLOPS_ARCHITECTURE_DIAGRAM.md](./MLOPS_ARCHITECTURE_DIAGRAM.md) file for the visual diagram and nodes flow.)*
**Step-by-Step Data Flow:**
1. **Ingestion**: Raw data (`iris.csv`) is managed via DVC. Binary blobs reside in MinIO; `.dvc` files are pushed to Bitbucket alongside source code.
2. **Triggering**: Jenkins performs an SCM poll against Bitbucket to detect changes and triggers the CI/CD Pipeline.
3. **Data Pull**: The specialized Jenkins Docker Agent pulls strictly the required raw CSV from MinIO.
4. **Validation**: `validate_data.py` enforces data schema and quality using Great Expectations.
5. **Training**: `train.py` executes utilizing Hydra for configs. It fetches data, trains a RandomForest model, logs system metrics and parameters to MLflow, and generates an Evidently AI report.
6. **Registry**: The trained model artifact is registered into the MLflow Model Registry.
7. **Artifact Build & Push (CI)**: Jenkins builds the API Docker image and packages the Kubernetes Helm charts, pushing them securely to the Nexus Repository.
8. **Deployment (CD)**: The Jenkins CD pipeline pulls the Helm charts from Nexus and connects to OpenShift. OpenShift fetches the Docker image directly from Nexus to spin up the FastAPI service natively within its cluster.
9. **Inference**: The active OpenShift Pod pulls the registered model on startup and exposes a `/predict` endpoint for real-time inference.

## 4. Detailed Component Design

### 4.1 Data Ingestion & Storage
- **Purpose**: Decouple large datasets from source code control to prevent repo bloat and enable precise versioning.
- **Tools**: DVC (Data Version Control), MinIO (S3 backend).
- **Internal Workflow**: DVC creates cryptographic hashes of datasets. Data is pushed to MinIO buckets (`dvc-storage`).
- **Failure Handling**: Network timeouts fallback to standard retry mechanisms; missing buckets are auto-provisioned via a `create_buckets` MinIO setup container on stack boot.

### 4.2 Data Validation
- **Purpose**: Ensure data entering the training pipeline strictly adheres to expected schemas to prevent silent model degradation.
- **Tools**: Great Expectations.
- **Internal Workflow**: A dedicated `validate_data.py` script pulls the dataset as a Pandas DataFrame, converting it to a Great Expectations DataFrame.
- **Inputs/Outputs**: Input: `data/raw/iris.csv`. Output: Binary Pass/Fail signal to Jenkins pipeline.
- **Failure Handling**: If schema expectations fail (e.g., missing columns, null values), `sys.exit(1)` propagates to Jenkins, failing the build instantly to prevent corrupt training.

### 4.3 Feature Store / Data Transformation
- **Purpose**: Manage and inject configuration parameters predictably.
- **Tools**: Hydra.
- **Internal Workflow**: `config.yaml` manages hyperparameters (`n_estimators`, `max_depth`), data splits (`test_size`), and file paths dynamically.

### 4.4 Training Pipeline
- **Purpose**: Fit the Machine Learning logic to validated data in a reproducible environment.
- **Tools**: Scikit-Learn, Pandas.
- **Internal Workflow**: Pipeline splits data, invokes the `RandomForestClassifier`, handles predictions on the test set, and generates multi-dimensional metrics (Accuracy, Precision, Recall, F1).
- **Scalability Considerations**: Standard Scikit-Learn logic; bound by single-node RAM. Future iterations may migrate to distributed architectures like Spark if datasets exceed memory bounds.

### 4.5 Model Evaluation & Observability
- **Purpose**: Track comprehensive run data and visualize real-time Data Drift and Model Performance.
- **Tools**: MLflow 3.x, Evidently AI.
- **Internal Workflow**: 
  - `mlflow.sklearn.autolog()` silently logs parameters and metrics.
  - `mlflow.set_system_metrics_sampling_interval(1)` traces CPU, RAM, and Disk metrics.
  - Evidently AI evaluates target drift and classification presets, outputting `evidently_report.html` as an MLflow artifact.

### 4.6 Model Registry
- **Purpose**: Provide a centralized, versioned, and auditable repository for production-ready model binaries.
- **Tools**: MLflow Registry.
- **Internal Workflow**: Models matching baseline heuristics are registered automatically under the name configured in Hydra (`Elite-Iris-Model`).

### 4.7 Deployment (Real-time)
- **Purpose**: Expose the trained model natively within an enterprise cluster environment as a highly available web service.
- **Tools**: FastAPI, Uvicorn, OpenShift, Helm, Nexus.
- **Internal Workflow**: Jenkins CD triggers OpenShift using standard Helm charts. OpenShift fetches the required Docker image from Nexus. `app.py` exposes a `/predict` POST endpoint. `@mlflow.trace` acts as a decorator to generate fine-grained latency spans for every inference request.
- **Inputs/Outputs**: JSON `IrisFeatures` in; JSON `PredictionResponse` out.
- **Failure Handling**: Fallback HTTP 500 exceptions if model artifacts are missing; 403 blocks for invalid API keys.

---

## 5. Data Architecture
- **Data Sources and Formats**: Flat CSV files for current scope; extensible to SQL/NoSQL stores.
- **Storage Solutions**: MinIO emulating an S3 Data Lake layer for unstructured or raw artifact storage.
- **Schema Design**: Strictly enforced tabular data: `sepal_length`, `sepal_width`, `petal_length`, `petal_width`, and `target`.
- **Data Versioning Strategy**: Cryptographically hashed blobs governed by DVC. A one-to-one mapping exists between a Git commit hash and a DVC data state.
- **Data Quality Checks**: Enforced synchronously via Great Expectations prior to any computational logic.

## 6. ML Pipeline Design

- **Training Pipeline Flow**: Check in Code -> Jenkins CI SCM Poll -> Env Setup -> Unit Tests -> Data Pull -> Validation -> **MLflow-Instrumented Training** -> Model Registration -> Nexus Artifact Push.
- **Orchestration Strategy**: Jenkins CI manages the training and artifact generation, while Jenkins CD manages the deployment to OpenShift.
- **Retraining Strategy**: Triggered via SCM polling on Bitbucket for data/code changes.
- **Experiment Tracking Methodology**: Centralized MLflow server tracking parameters, metrics, and system-level performance (psutil).
- **Reproducibility Strategy**: Data pinned via DVC; Code via Git; Environments via pinned Docker images and requirements.txt.

## 7. Deployment Architecture
- **Deployment Strategy**: Real-time synchronous API endpoint via FastAPI hosted on an OpenShift Cluster.
- **Infrastructure**: OpenShift cluster orchestrated via Helm. Components (MLflow, MinIO HA, and API) utilize **CephFS** (`openshift-storage.ceph.com/cephfs`) for high-performance, shared persistent storage.
- **Scaling Strategy**: Horizontal. Standard load balancers (e.g., Nginx, Traefik) can route traffic across replicated FastAPI instances.
- **Rollback Strategy**: Container immutability allows instant rollback to previous `elite-iris-api:latest` versions or specific Git tags.

## 8. CI/CD for ML (MLOps)

- **CI Pipeline**: Triggered via Jenkins SCM polling against Bitbucket. Executes linting, `pytest`, data pulls via DVC, schema validation, and training. 
  - **MLflow Integration**: During the training phase, the CI pipeline integrates with the centralized MLflow server to log hyperparameters, system metrics (CPU/RAM), training datasets, and performance reports. Upon success, it performs automated model registration.
  - **Artifact Generation**: Finally builds the Docker Image and Helm Charts, pushing them to Nexus.
- **CD Pipeline**: Operates independently. Triggered on successful CI or manual promotion. Pulls the Helm charts from Nexus, connects to OpenShift, and requests a deployment.
- **Automation Tools Used**: Jenkins (CI/CD server), Nexus Repository Manager, OpenShift pipelines/Helm.

## 9. Monitoring & Observability

- **Model Performance Monitoring**: Managed centrally via MLflow.
- **Data Drift Detection**: Evidently AI constructs an interactive HTML dashboard highlighting shifts between reference (train) and current (test/production) data distributions.
- **Logging and Alerting**: Structured JSON logging (`python-json-logger`) implemented across the FastAPI app. 
- **Telemetry System**: System exposes traces for inference execution using `mlflow.trace`. Prometheus and Grafana (integrated contextually) capture these exposed telemetry metrics.

## 10. Security & Compliance

- **Data Security**: Secure connection limits across the bridged Docker network. DVC and S3 buckets are password-protected via standard IAM-emulating MinIO credentials.
- **Access Control**: FastAPI route protected via robust `X-API-Key` headers.
- **Infrastructure Security**: Eliminated broad "Permission Denied" errors explicitly to enforce Docker's native volume security scopes, removing broad `chmod 777` paradigms. Strict hostname compliance limits DNS rebinding attack vectors in Werkzeug/MLflow.
- **Secrets Management**: Jenkins Credentials Provider securely injects variables (e.g., `API_KEY`) into runner environments without hardcoding them in the manifest.
- **Compliance**: Adheres to standard data privacy practices by ensuring raw datasets are never directly committed to source control.

## 11. Scalability & Performance

- **Load Handling**: Uvicorn ASGI server natively processes asynchronous requests, allowing high concurrent throughput on standard CPUs.
- **Latency Considerations**: Current MLflow traces mandate <50ms overhead per prediction, achieved by holding the RandomForest model strictly in memory once loaded (`load_cached_model`).
- **Bottleneck Analysis**: Potential disk I/O bottlenecks mitigated by moving MLflow tracking to an optimal `sqlite` disk volume vs frequent container memory wipes.

## 12. Failure Handling & Reliability

- **Fault Tolerance**: Docker containers enforce `restart: always` or orchestration logic to respawn immediately on internal failures.
- **Disaster Recovery**: MinIO S3 bucket data can be asynchronously backed up to cloud-native AWS S3 for geo-redundancy.
- **Network Resilience**: IP drift failures eradicated via static routing arrays.

## 13. Cost Optimization

- **Infrastructure Cost Considerations**: Local virtualization via Docker Compose, MinIO, and internal Jenkins removes direct OPEX costs commonly associated with managed Cloud ML architectures (like SageMaker or Vertex AI).
- **Optimization Strategies**: Artifact lifecycle rules should be instituted within MinIO to clear legacy or failed experiment artifacts reducing disk load securely over time.

## 14. Trade-offs & Design Decisions

- **Decision: Built-in MinIO S3 vs Public Cloud S3.**
  - *Why*: Allows for cost-free, offline development mirroring public cloud environments entirely.
  - *Trade-off*: Adds infrastructure maintenance overhead vs Managed AWS S3.
- **Decision: Jenkins vs GitHub Actions.**
  - *Why*: Enterprise-grade granular control over bare-metal executor agents and custom multi-stage Docker capabilities.
  - *Trade-off*: Higher visual complexity and setup cost compared to YAML-managed GitHub runners.
- **Decision: SQLite vs PostgreSQL for MLflow.**
  - *Why*: Reduced infrastructure weight for the baseline architecture. Limits scalable high-concurrency access directly to the DB, which is an accepted limitation for moderate team sizes.

## 15. Future Improvements
- **Model Shadowing**: Implement shadow deployment strategies to test new models silently against live production data before hot-swapping.
- **Kubernetes Migration**: Successfully translated `docker-compose.yml` into Helm Charts for genuine enterprise fault-tolerance and dynamic horizontal pod autoscaling. Components migrated:
  - **MLflow**: Optimized with external DB support and CephFS artifact storage.
  - **MinIO**: Deployed in Distributed Mode (HA) with 4 replicas on CephFS.
  - **Elite-Iris API**: Updated for multi-pod model sharing via CephFS ReadWriteMany volumes.
- **Real-Time Feature Store**: Evolve from flat `iris.csv` to Feast or Hopsworks for real-time feature retrieval during inference.
