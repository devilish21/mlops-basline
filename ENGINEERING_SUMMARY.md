# 🏛️ Elite-Iris MLOps Engineering Summary

This document consolidates the end-to-end development, stabilization, and architectural evolution of the Elite-Iris MLOps pipeline.

---

## A. ARCHITECTURE

**Components**
*   **Model Training & Validation:** Python scripts (`src/train.py`, `src/validate_model.py`) executing Scikit-Learn pipelines. Configuration managed via Hydra.
*   **Inference API:** FastAPI service (`app.py`) serving predictions, secured by API key authentication.
*   **Experiment Tracking & Registry:** MLflow Server tracking system metrics, runs, parameters, and providing model versioning.
*   **Data Version Control:** DVC tracking large files (e.g., `iris.csv`), shifting binary storage out of Git.
*   **Remote Blob Storage:** MinIO serving as the S3-compatible backend for DVC artifacts.
*   **CI/CD Automation:** Jenkins pipeline executing linting, data fetching, training, container building, and deployment using a customized Docker agent.

**Tools Used**
*   Python, FastAPI, Scikit-Learn, Pandas, Joblib
*   MLflow (v3.x observability, Fluent API)
*   DVC, MinIO (S3 Backend)
*   Docker, Docker Compose
*   Jenkins, Pytest, Hydra

**Data Flow**
1.  **Dev/Producer:** Developer updates `iris.csv`, adds it via DVC, and pushes to MinIO (`dvc-storage` bucket). Commits lightweight `.dvc` metadata to Git.
2.  **CI/Consumer:** Jenkins pipeline triggers on Git push. Uses a specialized Docker agent to pull the repo, then fetches specifically `iris.csv` from MinIO (`dvc pull data/raw/iris.csv`).
3.  **Training:** Jenkins runs `dvc repro`, triggering Hydra config resolution and MLflow tracking. The trained model is saved locally and registered in MLflow.
4.  **Deployment:** API Docker image is built. On the `main` branch, the API container is deployed, which loads the latest persistent model file for inference.

---

## B. SETUP

**Step-by-step pipeline setup:**
1.  **Infrastructure Initialization:** Execute `docker compose up -d` to spin up MLflow, MinIO, Jenkins, and a temporary `minio_setup` container (which auto-creates the `dvc-storage` bucket via the `mc` client).
2.  **DVC Remote Configuration:** Point DVC to the MinIO endpoint (`http://minio-s3:9000`), configuring the necessary S3 access credentials.
3.  **Data Pre-population:** Initialize data locally via `./dvc_host add data/raw/iris.csv` and `./dvc_host push` to upload the baseline dataset to MinIO.
4.  **Jenkins Agent Provisioning:** Build the `mlops-agent:latest` Docker image using the provided multi-stage `Dockerfile`. This ensures `dvc[s3]` functionality is baked into the CI environment.
5.  **Pipeline Construction:** Run the `Jenkinsfile` CI/CD pipeline, which executes sequentially: Setup → Test → DVC Pull → Train/Validate → Docker Build → Deploy.

---

## C. ISSUE–FIX TABLE

| Issue | Root Cause | Fix | Commit(s) |
| :--- | :--- | :--- | :--- |
| **Silent Training Failures** | Legacy MLflow 1.x logging lacked run-time metrics/tracing. | Implemented `mlflow.sklearn.autolog()`, `psutil`, and `@mlflow.trace`. | `a84a6c2`, `c7b77ab`, `f896b02` |
| **Experiment Init Errors** | Concurrent/repeated runs triggered DB conflicts. | Added defensive `try-except` blocks around experiment creation. | `b92d3f1` |
| **Unmanaged Model Artifacts** | Models were local files without registry versioning. | Implemented `mlflow.sklearn.log_model()` with registration args. | `bf632eb` |
| **Git Repo Bloat** | Binary datasets directly tracked in Git. | Initialized DVC tracking, redirecting binary storage to MinIO. | `f20c1da`, `102146e` |
| **Empty DVC Remote on Boot** | MinIO initializes without default buckets. | Added `create_buckets` container to auto-provision `dvc-storage`. | `d59e221` |
| **"Permission Denied" in CI** | Manual UID/GID mapping in `Jenkinsfile` broke host volume access. | Removed explicit user mapping, relying on Docker's native permissions. | `7d3858a` |
| **Missing S3 Drivers in CI** | Base python image lacked `dvc-s3` (Pip back-tracking loops). | Created multi-stage Dockerfile pinning `botocore` and `dvc-s3`. | `c62637d` |
| **"Invalid Endpoint" for MinIO**| S3 libs rejected `minio_s3` due to illegal DNS underscores. | Renamed container and config to hyphenated `minio-s3`. | `4d2d59e`, `1a7ed65` |
| **MLflow 403 DNS Rebinding** | MLflow/Werkzeug rejected `mlflow_server` due to underscores. | Renamed container and URIs to hyphenated `mlflow-server`. | `ac58b44` |
| **DVC Checkout Fails for Model**| First CI run tried to pull `model.joblib` before training. | Restricted `dvc pull` specifically to upstream dependency `iris.csv`. | `ed7d667` |
| **Tracking Timeouts** | Pytest hung connecting to missing/wrong MLflow URI. | Centralized global environments (`MLFLOW_TRACKING_URI`) in `Jenkinsfile`. | `1e05160` |
| **"Connection Refused" (IP Drift)**| Dynamic Docker IP assignment (`.2` vs `.3`) broke hardcoded configs. | Configured static IPAM subnet; pinned MLflow to `172.19.0.2`. | `19274a0`, `6ef3f3f`, `ac96edd` |

---

## D. EVOLUTION TIMELINE

1.  **Phase 1: Observability Elevation.** Upgraded from basic script logging to a comprehensive MLflow 3.x tracking system, adding deep latency tracing, system resource metrics, and model registry capabilities.
2.  **Phase 2: S3 Versioning Foundations.** Decoupled raw data from code by integrating DVC with an auto-provisioned MinIO backend, establishing a structured "Producer" workflow for datasets.
3.  **Phase 3: CI/CD Unblocking.** Resolved critical Jenkins automation blockers, fixing host/container filesystem permission errors and creating a highly optimized, S3-capable multi-stage agent image to bypass Python dependency hell.
4.  **Phase 4: Network Security & Stability.** Eliminated DNS-related security blocks (changing underscores to hyphens for S3/Werkzeug compliance) and eradicated intermittent connection failures by implementing deterministic, static IP subnetting across the Docker stack.

---

## E. FINAL STATE

**Stable Architecture:**
The pipeline achieves a fully synchronized, "zero-config" automated MLOps lifecycle. Developers safely push data changes via DVC, which Jenkins predictably consumes using an S3-enabled agent. Training runs are exhaustively logged (hardware metrics, code spans) in a physically pinned MLflow server (`172.19.0.2`), rendering the system completely immune to dynamic IP drift and DNS security exceptions.

**Key Lessons:**
*   **DNS Standard Conformance:** Underscores in container names (`minio_s3`, `mlflow_server`) will cause silent or confusing 403/Invalid Endpoint failures in strict web and cloud libraries. Always use standard hyphens.
*   **Agent Dependency Scope:** CI agent containers must be precision-built. Relying on dynamic `pip install` during runtime can lead to infinite dependency resolution loops (e.g., `botocore` vs `dvc-s3` conflicts). Multi-stage Docker builds with strict version pinning are mandatory.
*   **Deterministic Infrastructure:** Relying on Docker's dynamic IP allocation for intra-service communication across varied host reboots is brittle. Static IPAM or robust, hyphenated DNS routing is required for stable internal service discovery.
*   **CI Dependency Awareness:** CI pipelines must be state-aware. Blindly calling a global `dvc pull` will fail on fresh pipeline runs if downstream derived artifacts (like models) do not exist yet. Always scope data pulls strictly to raw upstream data.
