FROM python:3.9

# Install system dependencies
RUN apt-get update && apt-get install -y \
    make \
    git \
    curl \
    && curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash \
    && rm -rf /var/lib/apt/lists/*

# Pre-install Python dependencies
COPY requirements.txt /tmp/requirements.txt
# First install base requirements (without DVC which is moved to separate step)
RUN pip install --no-cache-dir "pathspec==0.11.2" \
    && pip install --no-cache-dir -r /tmp/requirements.txt
# Then force install DVC with S3 support using pinned versions to avoid resolution hell
RUN pip install --no-cache-dir "dvc-s3==3.1.0" "boto3==1.34.69" "botocore==1.34.69"

WORKDIR /app
