
pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        timeout(time: 20, unit: 'MINUTES')
    }

    triggers {
        pollSCM('H/5 * * * *')
    }

    environment {
        IMAGE_NAME = 'ronit87/github-gists-api'
        AWS_REGION = 'ap-southeast-2'
        EKS_CLUSTER_NAME = 'github-gists-eks'
        K8S_NAMESPACE = 'github-gists'
        DEPLOYMENT_NAME = 'github-gists-api'
        CONTAINER_NAME = 'github-gists-api'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm

                script {
                    env.IMAGE_TAG = sh(
                        script: 'git rev-parse HEAD',
                        returnStdout: true
                    ).trim()

                    echo "Building image: ${IMAGE_NAME}:${IMAGE_TAG}"
                }
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    set -e

                    docker run --rm \
                      --user "$(id -u):$(id -g)" \
                      -e PYTHONDONTWRITEBYTECODE=1 \
                      -v "$WORKSPACE:/app" \
                      -w /app \
                      python:3.13-slim \
                      python -m unittest discover -s tests -v
                '''
            }
        }

        stage('Build and Push Docker Image') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-credentials',
                        usernameVariable: 'DOCKERHUB_USERNAME',
                        passwordVariable: 'DOCKERHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu
                        set +x

                        export DOCKER_CONFIG="$(mktemp -d)"
                        chmod 700 "$DOCKER_CONFIG"

                        trap 'docker logout >/dev/null 2>&1 || true; rm -rf "$DOCKER_CONFIG"' EXIT

                        echo "$DOCKERHUB_TOKEN" | docker login \
                          --username "$DOCKERHUB_USERNAME" \
                          --password-stdin

                        docker build \
                          -t "$IMAGE_NAME:$IMAGE_TAG" .

                        docker push "$IMAGE_NAME:$IMAGE_TAG"

                        echo "Docker image pushed successfully"
                    '''
                }
            }
        }

        stage('Configure EKS') {
            steps {
                sh '''
                    set -e

                    echo "Verifying AWS identity"
                    aws sts get-caller-identity

                    aws eks update-kubeconfig \
                      --region "$AWS_REGION" \
                      --name "$EKS_CLUSTER_NAME"

                    kubectl auth can-i patch deployments \
                      -n "$K8S_NAMESPACE"
                '''
            }
        }

        stage('Update Docker Hub Pull Secret') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-credentials',
                        usernameVariable: 'DOCKERHUB_USERNAME',
                        passwordVariable: 'DOCKERHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu
                        set +x

                        export DOCKER_CONFIG="$(mktemp -d)"
                        chmod 700 "$DOCKER_CONFIG"

                        trap 'docker logout >/dev/null 2>&1 || true; rm -rf "$DOCKER_CONFIG"' EXIT

                        echo "$DOCKERHUB_TOKEN" | docker login \
                          --username "$DOCKERHUB_USERNAME" \
                          --password-stdin

                        kubectl create secret generic dockerhub-creds \
                          --namespace "$K8S_NAMESPACE" \
                          --type=kubernetes.io/dockerconfigjson \
                          --from-file=.dockerconfigjson="$DOCKER_CONFIG/config.json" \
                          --dry-run=client -o yaml | kubectl apply -f -
                    '''
                }
            }
        }

        stage('Deploy to EKS') {
            steps {
                sh '''
                    set -e

                    sed "s|IMAGE_PLACEHOLDER|${IMAGE_NAME}:${IMAGE_TAG}|g" \
                      k8s/deployment.yaml | kubectl apply -f -

                    kubectl rollout status \
                      deployment/"$DEPLOYMENT_NAME" \
                      --namespace="$K8S_NAMESPACE" \
                      --timeout=180s

                    kubectl get deployment "$DEPLOYMENT_NAME" \
                      --namespace="$K8S_NAMESPACE"
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                    set -eu

                    kubectl port-forward \
                      -n "$K8S_NAMESPACE" \
                      service/"$DEPLOYMENT_NAME" \
                      18080:80 > "$WORKSPACE/port-forward.log" 2>&1 &

                    PF_PID=$!
                    trap 'kill "$PF_PID" 2>/dev/null || true' EXIT

                    for i in $(seq 1 30); do
                        if curl -fsS --max-time 5 \
                          http://127.0.0.1:18080/health; then
                            echo "Application health check passed"
                            exit 0
                        fi

                        sleep 2
                    done

                    echo "Application health check failed"
                    cat "$WORKSPACE/port-forward.log"
                    exit 1
                '''
            }
        }
    }

    post {
        success {
            echo 'Build and deployment completed successfully.'
        }

        failure {
            echo 'Pipeline failed. Review the failed stage and console output.'
        }
    }
}
