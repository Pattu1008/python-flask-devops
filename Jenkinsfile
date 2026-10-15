
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
                bat 'docker build -t python-flask-app:1.0 .'
            }
        }

        stage('Verify Docker Image') {
            steps {
                bat 'docker images python-flask-app'
            }
        }

        stage('Verify Kubernetes Connection') {
            steps {
                withEnv(['KUBECONFIG=C:\\Users\\Prateek Sangle\\.kube\\config']) {
            bat 'kubectl config current-context'
            bat 'kubectl get nodes'
               }
            }
        }

        stage('Load Image into Kind') {
            steps {
                bat 'kind load docker-image python-flask-app:1.0 --name devops-lab'
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                bat 'kubectl config use-context kind-devops-lab'
                bat 'kubectl apply -f kubernetes/namespace.yaml'
                bat 'kubectl apply -f kubernetes/deployment.yaml'
                bat 'kubectl apply -f kubernetes/service.yaml'
            }
        }

        stage('Verify Deployment') {
            steps {
                bat 'kubectl rollout status deployment/flask-deployment -n devops-project --timeout=120s'
                bat 'kubectl get pods -n devops-project'
                bat 'kubectl get services -n devops-project'
            }
        }
    }

    post {
        success {
            echo 'Flask application deployed successfully to Kubernetes!'
        }

        failure {
            echo 'Pipeline failed. Check Console Output for the failing stage.'
        }
    }
}
