
pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        DOCKERHUB_REPO = 'ronit87/github-gists-api'
        IMAGE_NAME = 'github-gists-api'
    }

    stages {
        stage('Run Python Unit Tests') {
            steps {
                sh '''
                    set -eu

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

                    docker build \
                      -t "$IMAGE_NAME:$BUILD_NUMBER" .

                    docker images "$IMAGE_NAME"
                '''
            }
        }

        stage('Push Image to Docker Hub') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'gists-api-app-docker',
                        usernameVariable: 'DOCKERHUB_USER',
                        passwordVariable: 'DOCKERHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu
                        set +x

                        trap 'docker logout >/dev/null 2>&1 || true' EXIT

                        printf '%s' "$DOCKERHUB_TOKEN" |
                            docker login \
                                --username "$DOCKERHUB_USER" \
                                --password-stdin

                        docker tag \
                            "$IMAGE_NAME:$BUILD_NUMBER" \
                            "$DOCKERHUB_REPO:$BUILD_NUMBER"

                        docker push "$DOCKERHUB_REPO:$BUILD_NUMBER"
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "CI/CD image publishing succeeded: ${env.DOCKERHUB_REPO}:${env.BUILD_NUMBER}"
        }

        failure {
            echo 'Pipeline failed. Inspect Console Output for the first failing stage.'
        }

        always {
            echo "Build result: ${currentBuild.currentResult}"
        }
    }
}
