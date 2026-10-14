```groovy
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo 'Starting Flask project pipeline'
                checkout scm
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

        stage('Deploy Application') {
            steps {
                bat '''
                docker rm -f python-flask-container 2>NUL
                docker run -d --name python-flask-container -p 5000:5000 python-flask-app:1.0
                '''
            }
        }
    }
}
```