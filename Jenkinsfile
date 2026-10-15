pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo 'Starting Flask project pipeline'
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

        stage('Deploy Application') {
            steps {
                bat '''
                docker rm -f python-flask-container 2>NUL
                docker run -d --name python-flask-container -p 5000:5000 python-flask-app:1.0
                '''
            }
        }
        stage('Health Check') {
            steps {
               bat '''
               powershell -NoProfile -Command "$ok = $false; for ($i = 0; $i -lt 10; $i++) { try { $r = Invoke-WebRequest -Uri 'http://localhost:5000/' -UseBasicParsing -TimeoutSec 3; if ($r.StatusCode -eq 200) { $ok = $true; break } } catch { Start-Sleep -Seconds 3 } }; if (-not $ok) { docker logs python-flask-container; exit 1 }; Write-Output 'Health check passed: HTTP 200 OK'"
               '''
            }
        }
    }
}
