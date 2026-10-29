
pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        IMAGE_NAME = 'github-gists-api:local'
        CONTAINER_NAME = 'github-gists-api'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Run Tests') {
            steps {
                bat 'python -m pytest -v'
            }
        }

        stage('Build Docker Image') {
            steps {
                bat 'docker build -t %IMAGE_NAME% .'
            }
        }

        stage('Deploy Locally') {
            steps {
                bat '''
                    docker rm -f %CONTAINER_NAME% 2>NUL
                    docker run -d --name %CONTAINER_NAME% -p 127.0.0.1:8080:8080 %IMAGE_NAME%
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                powershell '''
                    $ready = $false

                    for ($i = 0; $i -lt 15; $i++) {
                        try {
                            $response = Invoke-WebRequest `
                                -Uri "http://127.0.0.1:8080/octocat" `
                                -TimeoutSec 3

                            if ($response.StatusCode -eq 200) {
                                $ready = $true
                                break
                            }
                        } catch {
                            Start-Sleep -Seconds 2
                        }
                    }

                    if (-not $ready) {
                        docker logs github-gists-api
                        throw "Local deployment smoke test failed"
                    }

                    Write-Host "Local deployment verified"
                '''
            }
        }
    }

    post {
        always {
            bat 'docker ps -a --filter name=github-gists-api'
        }
    }
}
