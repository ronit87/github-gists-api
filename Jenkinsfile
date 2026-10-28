
pipeline {
    agent any

    options {
        timestamps()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Run Python Unit Tests') {
            steps {
                sh '''
                    docker run --rm \
                      -v "$WORKSPACE:/app" \
                      -w /app \
                      python:3.12-slim \
                      python -m unittest discover -s tests -v
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    set -eu
                    docker build -t github-gists-api:${BUILD_NUMBER} .
                    docker images github-gists-api
                '''
            }
        }
    }

    post {
        success {
            echo 'CI passed: all Python unit tests succeeded.'
        }

        failure {
            echo 'CI failed: inspect the Console Output for the error.'
        }

        always {
            echo "Build result: ${currentBuild.currentResult}"
        }
    }
}
