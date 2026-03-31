# 📝 Elite-Iris-MLOps Project Changelog

This changelog documents the technical evolution and stabilization of the Elite-Iris-MLOps project, mapping each major architectural shift to the specific challenges resolved.

---

## 🏗️ Phase 1: Observability & MLflow 3.x Modernization
**Objective:** Transition to production-grade MLflow tracking and modern observability patterns.

| Context/Issue | Solution/Fix | Outcome |
| :--- | :--- | :--- |
| **Legacy Logging:** Basic MLflow 1.x logging lacked run-time metrics and tracing. | Implemented `mlflow.sklearn.autolog()` and added `psutil` for system metrics. | Full visibility into CPU/RAM usage and automated dataset tracking. |
| **Experiment Conflicts:** Fresh runs would often error if the experiment metadata was locked. | Added defensive `try-except` blocks for experiment initialization. | Robust pipeline restarts without manual database intervention. |
| **Silent Failures:** Critical training phases lacked detailed tracing. | Added `@mlflow.trace` (Fluent API) and manual spans for model loading. | Granular "Entity-Centric" UI in MLflow to debug specific run phases. |

---

## 📦 Phase 2: Data Versioning (DVC + MinIO)
**Objective:** Decouple data from code using S3-compatible remote storage.

| Context/Issue | Solution/Fix | Outcome |
| :--- | :--- | :--- |
| **Data Tracking:** Large CSV datasets were inflating the Git repository. | Initialized DVC tracking for `iris.csv` and created `.dvc` metadata pointers. | Git only tracks small pointers; binary data is moved to dedicated storage. |
| **Empty Remote:** MinIO bucket `dvc-storage` was not provisioned automatically. | Added a `create_buckets` (mc) container to `docker-compose`. | Automated infrastructure setup; first-time runs succeed without manual config. |
| **Silent Push:** Changes to data weren't always reflecting in the cloud. | Forced explicit manual tracking and configured the `./dvc_host` wrapper. | Developer-as-Producer model: verified data is guaranteed to be in MinIO before CI runs. |

---

## 🤖 Phase 3: CI/CD & Permission Hardening
**Objective:** Fixing Jenkins "Agent Hell" and container-to-host permissions.

| Context/Issue | Solution/Fix | Outcome |
| :--- | :--- | :--- |
| **Permission Denied:** Jenkins agent couldn't write to the host workspace. | Reverted UID/GID mapping and allowed Docker-managed volume permissions. | Seamless workspace access between the host and the CI container. |
| **Missing S3 Drivers:** Jenkins pipeline failed on `dvc pull` due to missing `dvc[s3]`. | Optimized `docker/agent/Dockerfile` with forced version pinning of S3 drivers. | CI container can now securely fetch data from MinIO using standard protocols. |
| **Recursive Deps:** Pip was hanging during agent builds for `botocore` resolution. | Multi-stage build with forced pins for `boto3` and `dvc-s3==3.1.0`. | Predictable and fast agent image builds; broken CI re-builders fixed. |

---

## 🌐 Phase 4: Infrastructure & Static Networking
**Objective:** Resolving the "DNS Rebinding" and "Connection Refused" issues.

| Context/Issue | Solution/Fix | Outcome |
| :--- | :--- | :--- |
| **Dynamic IPs:** Containers changed IPs on every restart, breaking tracking URIs. | Assigned static IP `172.19.0.2` to MLflow in `docker-compose`. | Rock-solid service discovery; tracked metadata always reaches the same store. |
| **DNS Rebinding:** Underscores in hostnames (`mlflow_server`) triggered 403 security errors. | Standardized all hostnames to DNS-compliant hyphens (`mlflow-server`). | Satisfied Werkzeug/S3 security checks across the entire Docker network. |
| **Endpoint Conflicts:** Host saw `127.0.0.1` but container needed internal IPs. | Synchronized `app.py`, `Jenkinsfile`, and `config.yaml` to the static IP. | "Universal Configuration": the same project code works on the host and in the cloud. |

---

## ✅ Current System Status
- **MLflow Tracking:** http://172.19.0.2:5000 (Internal) / http://localhost:5000 (Host)
- **MinIO S3:** http://minio-s3:9000 (Internal) / http://localhost:9000 (Host)
- **Jenkins Pipeline:** fully operational with automated testing, DVC pulling, and registration.
