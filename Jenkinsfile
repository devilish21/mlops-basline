pipeline {
    agent {
        docker {
            image 'python:3.9-slim'
            args '-u root'
        }
    }

    environment {
        REGISTRY = "localhost"
        IMAGE_NAME = "iris-api"
    }

    stages {
        stage('Install') {
            steps {
                sh 'apt-get update && apt-get install -y make git'
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Lint & Test') {
            steps {
                sh 'make ci'
            }
        }

        stage('Train') {
            steps {
                // This runs the complete DVC pipeline (data prep + training)
                sh 'dvc repro'
            }
        }

        stage('Build') {
            when {
                branch 'main'
            }
            steps {
                script {
                    sh "docker build -t ${IMAGE_NAME}:latest ."
                }
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                script {
                    // Remove existing container if it exists
                    sh "docker rm -f iris_api || true"
                    // Start the new container
                    sh "docker run -d --name iris_api -p 8000:8000 --network mlops_default -e MLFLOW_TRACKING_URI=http://mlflow:5000 -e API_KEY='enterprise-secret-key' ${IMAGE_NAME}:latest"
                }
            }
        }

        stage('Deploy Staging') {
            when {
                branch 'main'
            }
            steps {
                sh "helm upgrade --install iris-api-staging ./charts/iris-api --namespace staging --values ./charts/iris-api/values-staging.yaml"
            }
        }

        stage('Deploy Production') {
            when {
                branch 'main'
            }
            input {
                message "Deploy to Production?"
                ok "Deploy"
            }
            steps {
                sh "helm upgrade --install iris-api-prod ./charts/iris-api --namespace production --values ./charts/iris-api/values-production.yaml"
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
