pipeline {
    agent {
        docker {
            image 'mlops-agent:latest'
            args '-u 1000:1000 --network mlops_default'
        }
    }

    environment {
        REGISTRY = "localhost"
        IMAGE_NAME = "elite-iris-api"
        MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING = 'true'
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
                sh 'PYTHONPATH=. pytest tests/'
            }
        }

        stage('Train') {
            steps {
                sh 'dvc pull'
                sh 'dvc repro'
            }
        }

        stage('Validate') {
            steps {
                sh 'PYTHONPATH=. python src/validate_model.py'
            }
        }

        stage('Build') {
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


    }

    post {
        always {
            cleanWs()
        }
    }
}
