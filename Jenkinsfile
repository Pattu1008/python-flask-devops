pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo 'Starting Flask Kubernetes deployment pipeline'
                checkout scm
            }
        }

        stage('Run Python Tests') {
            steps {
                bat '"C:\\Users\\Prateek Sangle\\AppData\\Local\\Programs\\Python\\Python313\\python.exe" -m pip install -r requirements.txt'
                bat '"C:\\Users\\Prateek Sangle\\AppData\\Local\\Programs\\Python\\Python313\\python.exe" -m pytest -v'
            }
        }

        stage('Build Docker Image') {
            steps {
                bat 'docker build -t python-flask-app:1.1 .'
            }
        }

        stage('Verify Docker Image') {
            steps {
                bat 'docker images python-flask-app'
            }
        }

        stage('Load Image into Kind') {
            steps {
                bat '"C:\\Users\\Prateek Sangle\\AppData\\Local\\Programs\\kind\\kind.exe" load docker-image python-flask-app:1.1 --name devops-lab'
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                withEnv(['KUBECONFIG=C:\\Users\\Prateek Sangle\\.kube\\config']) {
                    bat 'kubectl config use-context kind-devops-lab'
                    bat 'kubectl apply -f kubernetes/namespace.yaml'
                    bat 'kubectl apply -f kubernetes/deployment.yaml'
                    bat 'kubectl apply -f kubernetes/service.yaml'
                }
            }
        }

        stage('Verify Deployment') {
            steps {
                withEnv(['KUBECONFIG=C:\\Users\\Prateek Sangle\\.kube\\config']) {
                    bat 'kubectl config current-context'
                    bat 'kubectl config view --minify -o jsonpath="{.clusters[0].cluster.server}"'
                    bat 'kubectl rollout status deployment/flask-deployment -n devops-project --timeout=120s'
                    bat 'kubectl get pods -n devops-project'
                    bat 'kubectl get services -n devops-project'
                }
            }
        }

        stage('Create Monitoring Namespace') {
            steps {
                withEnv(['KUBECONFIG=C:\\Users\\Prateek Sangle\\.kube\\config']) {
                    bat 'kubectl apply -f kubernetes/monitoring-namespace.yaml'
                }
            }
        }

        stage('Deploy Prometheus') {
            steps {
                withEnv(['KUBECONFIG=C:\\Users\\Prateek Sangle\\.kube\\config']) {
                    bat 'kubectl apply -f observability/prometheus/prometheus-configmap.yaml'
                    bat 'kubectl apply -f observability/prometheus/prometheus-deployment.yaml'
                    bat 'kubectl apply -f observability/prometheus/prometheus-service.yaml'
                }
            }
        }

        stage('Deploy Grafana') {
            steps {
                withEnv(['KUBECONFIG=C:\\Users\\Prateek Sangle\\.kube\\config']) {
                    bat 'kubectl apply -f observability/grafana/grafana-datasource.yaml'
                    bat 'kubectl apply -f observability/grafana/grafana-deployment.yaml'
                    bat 'kubectl apply -f observability/grafana/grafana-service.yaml'
                }
            }
        }

        stage('Verify Monitoring') {
            steps {
                withEnv(['KUBECONFIG=C:\\Users\\Prateek Sangle\\.kube\\config']) {
                    bat 'kubectl get configmap -n monitoring'
                    bat 'kubectl get deployments -n monitoring'
                    bat 'kubectl get pods -n monitoring'
                    bat 'kubectl get services -n monitoring'
                }
            }
        }
    }

    post {
        success {
            echo 'Flask application and monitoring resources deployed successfully!'
        }

        failure {
            echo 'Pipeline failed. Check Console Output for the failing stage.'
        }
    }
}