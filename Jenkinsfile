pipeline {
    agent {
        docker {
            image 'mlops-agent:latest'
            args '-u root --network mlops_default'
        }
    }

    environment {
        REGISTRY = "localhost"
        IMAGE_NAME = "elite-iris-api"
    }

    stages {
        stage('Initialize') {
            steps {
                sh 'python --version'
                sh 'make --version'
            }
        }

        stage('Lint & Test') {
            steps {
                sh 'python -m flake8 src/ app.py'
                sh 'PYTHONPATH=. pytest tests/'
            }
        }

        stage('Train') {
            steps {
                sh 'dvc repro'
            }
        }

        stage('Validate') {
            steps {
                sh 'PYTHONPATH=. python src/validate_model.py'
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
                sh "helm upgrade --install elite-iris-api-staging ./charts/elite-iris-api --namespace staging --values ./charts/elite-iris-api/values-staging.yaml"
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
                sh "helm upgrade --install elite-iris-api-prod ./charts/elite-iris-api --namespace production --values ./charts/elite-iris-api/values-production.yaml"
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
