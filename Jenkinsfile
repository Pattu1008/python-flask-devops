
pipeline {
    agent any

    environment {
        IMAGE_NAME = 'python-flask-app'
        IMAGE_TAG = "${BUILD_NUMBER}"
        K8S_NAMESPACE = 'devops-project'
        MONITORING_NAMESPACE = 'monitoring'
        KIND_CLUSTER = 'devops-lab'
        KUBECONFIG = 'C:\\Users\\Prateek Sangle\\.kube\\config'
        PYTHON = 'C:\\Users\\Prateek Sangle\\AppData\\Local\\Programs\\Python\\Python313\\python.exe'
        KIND_EXE = 'C:\\Users\\Prateek Sangle\\AppData\\Local\\Programs\\kind\\kind.exe'
        HELM_EXE = 'C:\\Users\\Prateek Sangle\\bin\\helm.exe'
        TRIVY_EXE = 'C:\\Users\\Prateek Sangle\\bin\\trivy.exe'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Starting Flask testing, database migration, deployment, and monitoring pipeline'
                checkout scm
            }
        }

        stage('Automated Unit Tests and Coverage') {
            steps {
                bat 'if not exist reports mkdir reports'
                bat '"%PYTHON%" -m pip install -r requirements.txt'
                bat '"%PYTHON%" -m pip install pytest pytest-cov junit2html'

                bat '"%PYTHON%" -m pytest tests/ -v --junitxml=reports\\unit-tests.xml --cov=app --cov-report=xml:reports\\coverage.xml --cov-report=html:reports\\coverage-html'

                powershell '''
                    $python = $env:PYTHON
                    $scripts = Join-Path (Split-Path $python) "Scripts"
                    $converter = Join-Path $scripts "junit2html.exe"

                    if (-not (Test-Path $converter)) {
                        & $python -m pip install junit2html
                        if ($LASTEXITCODE -ne 0) {
                            throw "Failed to install junit2html"
                        }
                    }

                    if (-not (Test-Path $converter)) {
                        throw "junit2html executable not found: $converter"
                    }

                    & $converter "reports/unit-tests.xml" "reports/unit-tests.html"

                    if ($LASTEXITCODE -ne 0) {
                        throw "Failed to generate unit test HTML report"
                    }
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                bat 'docker build -t %IMAGE_NAME%:%IMAGE_TAG% .'
            }
        }

        stage('Trivy Dependency Scan') {
            steps {
                bat 'if not exist reports mkdir reports'

                bat '''
                    "%TRIVY_EXE%" fs ^
                      --scanners vuln ^
                      --format json ^
                      --output reports\\trivy-fs.json ^
                      --exit-code 0 ^
                      --no-progress ^
                      .
                '''
            }
        }

        stage('Trivy Image Scan') {
            steps {
                bat '''
                    "%TRIVY_EXE%" image ^
                      --scanners vuln ^
                      --format json ^
                      --output reports\\trivy-image.json ^
                      --exit-code 0 ^
                      --no-progress ^
                      %IMAGE_NAME%:%IMAGE_TAG%
                '''
            }
        }

        stage('Generate Trivy HTML Reports') {
            steps {
                bat 'if not exist reports mkdir reports'

                powershell '''
                    $templatePath = Join-Path $env:WORKSPACE 'templates\\html.tpl'

                    if (-not (Test-Path $templatePath)) {
                        New-Item -ItemType Directory -Force `
                            -Path (Split-Path $templatePath) | Out-Null

                        Invoke-WebRequest `
                            -Uri 'https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/html.tpl' `
                            -OutFile $templatePath
                    }

                    if (-not (Test-Path $templatePath) -or
                        (Get-Item $templatePath).Length -eq 0) {
                        throw 'Trivy HTML template is missing or empty.'
                    }
                '''

                bat '''
                    "%TRIVY_EXE%" fs ^
                      --scanners vuln ^
                      --format template ^
                      --template "@templates/html.tpl" ^
                      --output reports\\trivy-fs.html ^
                      --exit-code 0 ^
                      --no-progress ^
                      .
                    if errorlevel 1 exit /b 1

                    "%TRIVY_EXE%" image ^
                      --scanners vuln ^
                      --format template ^
                      --template "@templates/html.tpl" ^
                      --output reports\\trivy-image.html ^
                      --exit-code 0 ^
                      --no-progress ^
                      %IMAGE_NAME%:%IMAGE_TAG%
                    if errorlevel 1 exit /b 1
                '''
            }
        }

        stage('Trivy Security Gate') {
            steps {
                powershell '''
                    $reportPaths = @(
                        "reports/trivy-fs.json",
                        "reports/trivy-image.json"
                    )

                    $critical = @()

                    foreach ($path in $reportPaths) {
                        if (-not (Test-Path $path)) {
                            throw "Trivy report is missing: $path"
                        }

                        $report = Get-Content $path -Raw | ConvertFrom-Json

                        foreach ($result in $report.Results) {
                            foreach ($vuln in $result.Vulnerabilities) {
                                if ($vuln.Severity -eq "CRITICAL") {
                                    $critical += [PSCustomObject]@{
                                        Report        = $path
                                        Target        = $result.Target
                                        Vulnerability = $vuln.VulnerabilityID
                                        Package       = $vuln.PkgName
                                        Installed     = $vuln.InstalledVersion
                                        Fixed         = $vuln.FixedVersion
                                    }
                                }
                            }
                        }
                    }

                    if ($critical.Count -gt 0) {
                        $critical | Format-Table -AutoSize | Out-String | Write-Host
                        throw "Security gate failed: critical vulnerabilities detected."
                    }

                    Write-Host "Security gate passed: no critical vulnerabilities detected."
                '''
            }
        }

        stage('Verify Docker Image') {
            steps {
                bat 'docker image inspect %IMAGE_NAME%:%IMAGE_TAG%'
            }
        }

        stage('API Tests with Newman') {
            steps {
                script {
                    try {
                        bat 'docker rm -f flask-api-test >NUL 2>&1 || exit /b 0'
                        bat 'docker run -d --name flask-api-test -p 5001:5000 %IMAGE_NAME%:%IMAGE_TAG%'

                        powershell '''
                            $ready = $false

                            for ($i = 0; $i -lt 30; $i++) {
                                try {
                                    $response = Invoke-RestMethod `
                                        -Uri "http://localhost:5001/health" `
                                        -TimeoutSec 3

                                    if ($response.status -eq "healthy") {
                                        $ready = $true
                                        break
                                    }
                                }
                                catch {
                                    Start-Sleep -Seconds 2
                                }
                            }

                            if (-not $ready) {
                                docker logs flask-api-test
                                throw "Flask API did not become healthy on port 5001."
                            }

                            Write-Host "Flask API is healthy."
                        '''

                        bat '''
                            docker run --rm ^
                              -v "%WORKSPACE%\\postman:/etc/newman:ro" ^
                              -v "%WORKSPACE%\\reports:/reports" ^
                              node:24-slim ^
                              sh -c "npm install -g newman && newman run /etc/newman/flask-api-tests.json --env-var baseUrl=http://host.docker.internal:5001 --reporters cli,junit --reporter-junit-export /reports/api-tests.xml"
                        '''

                        powershell '''
                            $python = $env:PYTHON
                            $scripts = Join-Path (Split-Path $python) "Scripts"
                            $converter = Join-Path $scripts "junit2html.exe"

                            if (-not (Test-Path $converter)) {
                                & $python -m pip install junit2html
                                if ($LASTEXITCODE -ne 0) {
                                    throw "Failed to install junit2html"
                                }
                            }

                            if (-not (Test-Path $converter)) {
                                throw "junit2html executable not found: $converter"
                            }

                            & $converter "reports/api-tests.xml" "reports/api-tests.html"

                            if ($LASTEXITCODE -ne 0) {
                                throw "Failed to generate API test HTML report"
                            }
                        '''
                    }
                    finally {
                        bat 'docker rm -f flask-api-test >NUL 2>&1 || exit /b 0'
                    }
                }
            }
        }

        stage('Database Migration with Flyway') {
            steps {
                bat 'if not exist reports mkdir reports'

                withCredentials([
                    usernamePassword(
                        credentialsId: 'db-credentials',
                        usernameVariable: 'DB_USER',
                        passwordVariable: 'DB_PASSWORD'
                    )
                ]) {
                    bat '''
                        @echo off
                        set "FLYWAY_URL=jdbc:postgresql://migration-postgres:5432/flaskdb"
                        set "FLYWAY_USER=%DB_USER%"
                        set "FLYWAY_PASSWORD=%DB_PASSWORD%"

                        docker network inspect python-project_default >NUL 2>&1
                        if errorlevel 1 (
                            echo ERROR: Docker network python-project_default was not found.
                            echo Check the network using docker network ls.
                            exit /b 1
                        )

                        docker run --rm --network python-project_default ^
                          -e FLYWAY_URL -e FLYWAY_USER -e FLYWAY_PASSWORD ^
                          -v "%WORKSPACE%\\migrations:/flyway/sql:ro" ^
                          flyway/flyway:11 migrate > reports\\migration.log 2>&1

                        set "MIGRATE_RESULT=%ERRORLEVEL%"
                        type reports\\migration.log

                        if not "%MIGRATE_RESULT%"=="0" exit /b %MIGRATE_RESULT%

                        docker run --rm --network python-project_default ^
                          -e FLYWAY_URL -e FLYWAY_USER -e FLYWAY_PASSWORD ^
                          -v "%WORKSPACE%\\migrations:/flyway/sql:ro" ^
                          flyway/flyway:11 info > reports\\migration-info.log 2>&1

                        set "INFO_RESULT=%ERRORLEVEL%"
                        type reports\\migration-info.log
                        exit /b %INFO_RESULT%
                    '''
                }
            }
        }

        stage('Load Image into Kind') {
            steps {
                bat '"%KIND_EXE%" load docker-image %IMAGE_NAME%:%IMAGE_TAG% --name %KIND_CLUSTER%'
            }
        }

        stage('Create Application Namespace') {
            steps {
                bat 'kubectl config use-context kind-devops-lab'
                bat 'kubectl apply -f kubernetes/namespace.yaml'
            }
        }

        stage('Deploy Application to Kubernetes') {
            steps {
                powershell '''
                    $manifest = Get-Content "kubernetes/deployment.yaml" -Raw
                    $manifest = $manifest -replace 'python-flask-app:[^\\s]+', "python-flask-app:$env:IMAGE_TAG"
                    Set-Content -Path "kubernetes/deployment.rendered.yaml" -Value $manifest
                '''

                bat 'kubectl apply -f kubernetes/deployment.rendered.yaml'
                bat 'kubectl apply -f kubernetes/service.yaml'
            }
        }

        stage('Verify Application Deployment') {
            steps {
                bat 'kubectl rollout status deployment/flask-deployment -n %K8S_NAMESPACE% --timeout=180s'
                bat 'kubectl get deployment flask-deployment -n %K8S_NAMESPACE%'
                bat 'kubectl get pods -n %K8S_NAMESPACE%'
                bat 'kubectl get services -n %K8S_NAMESPACE%'

                bat 'kubectl exec deployment/flask-deployment -n %K8S_NAMESPACE% -- python -c "import urllib.request; print(urllib.request.urlopen(\'http://localhost:5000/health\', timeout=5).read().decode()); print(\'Metrics HTTP status:\', urllib.request.urlopen(\'http://localhost:5000/metrics\', timeout=5).status)"'
            }
        }

        stage('Create Monitoring Namespace') {
            steps {
                bat 'kubectl apply -f kubernetes/monitoring-namespace.yaml'
            }
        }

        stage('Install Blackbox Exporter') {
            steps {
                bat '"%HELM_EXE%" repo add prometheus-community https://prometheus-community.github.io/helm-charts --force-update'
                bat '"%HELM_EXE%" repo update'
                bat '"%HELM_EXE%" upgrade --install blackbox prometheus-community/prometheus-blackbox-exporter --namespace %MONITORING_NAMESPACE% --create-namespace --wait --timeout 180s'
                bat 'kubectl rollout status deployment/blackbox-prometheus-blackbox-exporter -n %MONITORING_NAMESPACE% --timeout=180s'
                bat 'kubectl get svc blackbox-prometheus-blackbox-exporter -n %MONITORING_NAMESPACE%'
            }
        }

        stage('Deploy Node Exporter') {
            steps {
                echo 'Deploying Node Exporter for node-level metrics'
                bat 'kubectl apply -f observability/node-exporter.yaml'
                bat 'kubectl rollout status daemonset/node-exporter -n %MONITORING_NAMESPACE% --timeout=180s'
                bat 'kubectl get daemonset node-exporter -n %MONITORING_NAMESPACE%'
                bat 'kubectl get pods,svc -n %MONITORING_NAMESPACE% -l app=node-exporter'
            }
        }

        stage('Install kube-state-metrics') {
            steps {
                echo 'Installing Kubernetes object-state metrics'
                bat '"%HELM_EXE%" upgrade --install kube-state-metrics prometheus-community/kube-state-metrics --namespace %MONITORING_NAMESPACE% --create-namespace --wait --timeout 180s'
                bat 'kubectl rollout status deployment/kube-state-metrics -n %MONITORING_NAMESPACE% --timeout=180s'
                bat 'kubectl get deployment kube-state-metrics -n %MONITORING_NAMESPACE%'
                bat 'kubectl get pods,svc -n %MONITORING_NAMESPACE% -l app.kubernetes.io/name=kube-state-metrics'
            }
        }

        stage('Deploy Prometheus') {
            steps {
                bat 'kubectl apply -f observability/prometheus/prometheus-configmap.yaml'
                bat 'kubectl apply -f observability/prometheus/prometheus-deployment.yaml'
                bat 'kubectl apply -f observability/prometheus/prometheus-service.yaml'
                bat 'kubectl rollout restart deployment/prometheus -n %MONITORING_NAMESPACE%'
                bat 'kubectl rollout status deployment/prometheus -n %MONITORING_NAMESPACE% --timeout=180s'
            }
        }

        stage('Deploy Loki and Alloy') {
            steps {
                echo 'Deploying Loki log storage'
                bat 'kubectl apply -f observability/loki/loki.yaml'
                bat 'kubectl rollout status deployment/loki -n %MONITORING_NAMESPACE% --timeout=180s'

                echo 'Deploying Grafana Alloy log collector'
                bat 'kubectl apply -f observability/alloy/alloy.yaml'
                bat 'kubectl rollout status deployment/alloy -n %MONITORING_NAMESPACE% --timeout=180s'
                bat 'kubectl get pods,svc -n %MONITORING_NAMESPACE%'
            }
        }

        stage('Deploy Grafana') {
            steps {
                echo 'Applying combined Prometheus and Loki datasource configuration'
                bat 'kubectl apply -f observability/grafana/grafana-datasource.yaml'
                bat 'kubectl apply -f observability/grafana/grafana-deployment.yaml'
                bat 'kubectl apply -f observability/grafana/grafana-service.yaml'
                bat 'kubectl rollout status deployment/grafana -n %MONITORING_NAMESPACE% --timeout=180s'
                bat 'kubectl get deployment grafana -n %MONITORING_NAMESPACE%'
                bat 'kubectl get pods -n %MONITORING_NAMESPACE% -l app=grafana'
            }
        }

        stage('Deploy Monitoring Proxy') {
            steps {
                bat 'kubectl apply -f kubernetes/monitoring-proxy.yaml'
                bat 'kubectl rollout status deployment/monitoring-proxy -n %MONITORING_NAMESPACE% --timeout=120s'
                bat 'kubectl get deployment,pods,svc -n %MONITORING_NAMESPACE%'
            }
        }

        stage('Expose Monitoring Dashboards') {
            steps {
                bat 'docker compose -f docker-compose.monitoring-proxy.yml config -q'
                bat 'docker inspect --format="{{.State.Status}}" monitoring-host-proxy'
                bat 'docker port monitoring-host-proxy'
            }
        }

        stage('Verify Monitoring Dashboard Access') {
            steps {
                bat 'powershell -NoProfile -Command "$ProgressPreference=\'SilentlyContinue\'; (Invoke-WebRequest http://localhost:9090/-/ready -TimeoutSec 10 -UseBasicParsing).Content"'
                bat 'powershell -NoProfile -Command "$ProgressPreference=\'SilentlyContinue\'; (Invoke-WebRequest http://localhost:3000/api/health -TimeoutSec 10 -UseBasicParsing).Content"'
            }
        }
    }

    post {
        always {
            // Native Jenkins test results
            junit testResults: 'reports/*-tests.xml', allowEmptyResults: true

            // Unit test HTML
            publishHTML(target: [
                reportName: 'Unit Test HTML Report',
                reportDir: 'reports',
                reportFiles: 'unit-tests.html',
                keepAll: true,
                alwaysLinkToLastBuild: true,
                allowMissing: true
            ])

            // API test HTML
            publishHTML(target: [
                reportName: 'API Test HTML Report',
                reportDir: 'reports',
                reportFiles: 'api-tests.html',
                keepAll: true,
                alwaysLinkToLastBuild: true,
                allowMissing: true
            ])

            // Code coverage HTML
            publishHTML(target: [
                reportName: 'Code Coverage Report',
                reportDir: 'reports/coverage-html',
                reportFiles: 'index.html',
                keepAll: true,
                alwaysLinkToLastBuild: true,
                allowMissing: true
            ])

            // Trivy filesystem scan HTML
            publishHTML(target: [
                reportName: 'Trivy Filesystem Security Report',
                reportDir: 'reports',
                reportFiles: 'trivy-fs.html',
                keepAll: true,
                alwaysLinkToLastBuild: true,
                allowMissing: true
            ])

            // Trivy image scan HTML
            publishHTML(target: [
                reportName: 'Trivy Image Security Report',
                reportDir: 'reports',
                reportFiles: 'trivy-image.html',
                keepAll: true,
                alwaysLinkToLastBuild: true,
                allowMissing: true
            ])

            // Archive all reports
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
        }

        success {
            echo "Deployment successful! Image: python-flask-app:${env.IMAGE_TAG}"
            echo 'Prometheus: http://localhost:9090/targets'
            echo 'Grafana: http://localhost:3000'
        }

        failure {
            echo 'Pipeline failed. Check Console Output for the failing stage.'
        }
    }
}
