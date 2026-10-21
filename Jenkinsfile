pipeline {
    agent any

    environment {
        IMAGE_NAME = 'python-flask-app'
        K8S_NAMESPACE = 'devops-project'
        MONITORING_NAMESPACE = 'monitoring'
        KIND_CLUSTER = 'devops-lab'
        KUBECONFIG = 'C:\\Users\\Prateek Sangle\\.kube\\config'
        PYTHON = 'C:\\Users\\Prateek Sangle\\AppData\\Local\\Programs\\Python\\Python313\\python.exe'
        KIND_EXE = 'C:\\Users\\Prateek Sangle\\AppData\\Local\\Programs\\kind\\kind.exe'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Starting Flask Kubernetes deployment pipeline'
                checkout scm
                script {
                    env.IMAGE_TAG = "${env.BUILD_NUMBER}"
                    echo "Docker image: ${env.IMAGE_NAME}:${env.IMAGE_TAG}"
                }
            }
        }

        stage('Run Python Tests') {
            steps {
                bat '"%PYTHON%" -m pip install -r requirements.txt'
                bat '"%PYTHON%" -m pytest -v'
            }
        }

        stage('Build Docker Image') {
            steps {
                bat 'docker build -t %IMAGE_NAME%:%IMAGE_TAG% .'
            }
        }

        stage('Verify Docker Image') {
            steps {
                bat 'docker image inspect %IMAGE_NAME%:%IMAGE_TAG%'
            }
        }

        stage('Load Image into Kind') {
            steps {
                bat '"%KIND_EXE%" load docker-image %IMAGE_NAME%:%IMAGE_TAG% --name %KIND_CLUSTER%'
            }
        }

        stage('Deploy Application to Kubernetes') {
            steps {
                bat 'kubectl config use-context kind-devops-lab'
                bat 'kubectl apply -f kubernetes/namespace.yaml'

                // Update the deployment to use this build's image tag.
                powershell '''
                    $manifest = Get-Content "kubernetes/deployment.yaml" -Raw
                    $manifest = $manifest -replace 'python-flask-app:[^\\s]+', "python-flask-app:$env:IMAGE_TAG"
                    Set-Content -Path "kubernetes/deployment.rendered.yaml" -Value $manifest
                '''

                bat 'kubectl apply -f kubernetes/deployment.rendered.yaml'
                bat 'kubectl apply -f kubernetes/service.yaml'
                bat 'kubectl apply -f kubernetes/monitoring-proxy.yaml'
                bat 'kubectl rollout status deployment/monitoring-proxy -n monitoring --timeout=120s'
            }
        }

        stage('Verify Application Deployment') {
            steps {
                bat 'kubectl config current-context'
                bat 'kubectl rollout status deployment/flask-deployment -n %K8S_NAMESPACE% --timeout=180s'
                bat 'kubectl get deployment flask-deployment -n %K8S_NAMESPACE%'
                bat 'kubectl get pods -n %K8S_NAMESPACE%'
                bat 'kubectl get services -n %K8S_NAMESPACE%'

                // Verify both health and Prometheus metrics endpoints.
                bat 'kubectl exec deployment/flask-deployment -n %K8S_NAMESPACE% -- python -c "import urllib.request; print(urllib.request.urlopen(\'http://localhost:5000/health\', timeout=5).read().decode()); print(\'Metrics HTTP status:\', urllib.request.urlopen(\'http://localhost:5000/metrics\', timeout=5).status)"'
            }
        }

        stage('Create Monitoring Namespace') {
            steps {
                bat 'kubectl apply -f kubernetes/monitoring-namespace.yaml'
            }
        }

        stage('Deploy Prometheus') {
            steps {
                bat 'kubectl apply -f observability/prometheus/prometheus-configmap.yaml'
                bat 'kubectl apply -f observability/prometheus/prometheus-deployment.yaml'
                bat 'kubectl apply -f observability/prometheus/prometheus-service.yaml'

                // Restart Prometheus to load an updated configuration.
                bat 'kubectl rollout restart deployment/prometheus -n %MONITORING_NAMESPACE%'
                bat 'kubectl rollout status deployment/prometheus -n %MONITORING_NAMESPACE% --timeout=180s'
            }
        }

        stage('Deploy Grafana') {
            steps {
                bat 'kubectl apply -f observability/grafana/grafana-datasource.yaml'
                bat 'kubectl apply -f observability/grafana/grafana-deployment.yaml'
                bat 'kubectl apply -f observability/grafana/grafana-service.yaml'
                bat 'kubectl rollout status deployment/grafana -n %MONITORING_NAMESPACE% --timeout=180s'
            }
        }

        stage('Verify Monitoring') {
            steps {
                bat 'kubectl get configmap -n %MONITORING_NAMESPACE%'
                bat 'kubectl get deployments -n %MONITORING_NAMESPACE%'
                bat 'kubectl get pods -n %MONITORING_NAMESPACE%'
                bat 'kubectl get services -n %MONITORING_NAMESPACE%'
            }
        }
    }

    post {
        success {
            echo "Deployment successful! Image: python-flask-app:${env.IMAGE_TAG}"
        }

        failure {
            echo 'Pipeline failed. Check Console Output for the failing stage.'
        }
    }
}
