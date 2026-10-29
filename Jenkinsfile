
pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        DOCKERHUB_REPO = 'ronit87/github-gists-api'
        IMAGE_NAME = 'github-gists-api'

        EC2_HOST = 'ec2-3-107-31-5.ap-southeast-2.compute.amazonaws.com'
        EC2_USER = 'ec2-user'
        CONTAINER_NAME = 'github-gists-api'
        APP_PORT = '8080'
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

        stage('Deploy to EC2') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'gists-api-app-docker',
                        usernameVariable: 'DOCKERHUB_USER',
                        passwordVariable: 'DOCKERHUB_TOKEN'
                    )
                ]) {
                    sshagent(credentials: ['ec2-ssh-key']) {
                        sh '''
                            set -eu
                            set +x

                            EC2_TARGET="${EC2_USER}@${EC2_HOST}"
                            IMAGE="${DOCKERHUB_REPO}:${BUILD_NUMBER}"

                            # Authenticate to Docker Hub on EC2.
                            printf '%s' "$DOCKERHUB_TOKEN" |
                                ssh \
                                    -o BatchMode=yes \
                                    -o StrictHostKeyChecking=yes \
                                    "$EC2_TARGET" \
                                    "docker login --username '$DOCKERHUB_USER' --password-stdin"

                            # Pull the exact image published by this build.
                            # Replace the existing container and verify it runs.
                            ssh \
                                -o BatchMode=yes \
                                -o StrictHostKeyChecking=yes \
                                "$EC2_TARGET" \
                                "set -eu
                                 trap 'docker logout >/dev/null 2>&1 || true' EXIT

                                 docker pull '$IMAGE'

                                 docker rm -f '$CONTAINER_NAME' \
                                     >/dev/null 2>&1 || true

                                 docker run -d \
                                     --name '$CONTAINER_NAME' \
                                     --restart unless-stopped \
                                     -p '$APP_PORT:$APP_PORT' \
                                     '$IMAGE'

                                 sleep 3

                                 docker ps \
                                     --filter 'name=^/${CONTAINER_NAME}$' \
                                     --filter 'status=running' \
                                     --format '{{.Names}}' |
                                     grep -Fx '$CONTAINER_NAME'
                                "
                        '''
                    }
                }
            }
        }
    }

    post {
        success {
            echo "CI/CD succeeded: ${env.DOCKERHUB_REPO}:${env.BUILD_NUMBER}"
            echo "Deployed container: ${env.CONTAINER_NAME}"
        }

        failure {
            echo 'Pipeline failed. Inspect Console Output for the first failing stage.'
        }

        always {
            echo "Build result: ${currentBuild.currentResult}"
        }
    }
}
