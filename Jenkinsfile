    pipeline {
        agent any

        // Define interactive parameters for the Jenkins UI
        parameters {
            string(name: 'SCALE_COUNT', defaultValue: '3', description: 'Number of Flask app instances to run behind Nginx')
        }

        environment {
            DOCKER_REGISTRY_USER = 'koriaryan'
            IMAGE_NAME           = 'library_app'
            IMAGE_TAG            = 'latest'
            DOCKER_HUB_CREDS     = credentials('docker-hub-creds')
        }

        stages {
            stage('Checkout') {
                steps {
                    checkout scm
                }
            }

            stage('Build Image') {
                steps {
                    echo 'Building Docker image...'
                    bat """
                    docker build -t %DOCKER_REGISTRY_USER%/%IMAGE_NAME%:%IMAGE_TAG% .
                    """
                }
            }

            stage('Push to Docker Hub') {
                steps {
                    echo 'Logging in to Docker Hub and pushing image...'
                    bat """
                    echo %DOCKER_HUB_CREDS_PSW% | docker login -u %DOCKER_HUB_CREDS_USR% --password-stdin
                    docker push %DOCKER_REGISTRY_USER%/%IMAGE_NAME%:%IMAGE_TAG%
                    """
                }
            }

            stage('Deploy (Pull, Compose & Scale)') {
                steps {
                    echo 'Stopping existing deployment...'
                    bat """
                    set DOCKER_REGISTRY_USER=%DOCKER_REGISTRY_USER%
                    docker compose down
                    """

                    echo 'Pulling fresh image from Docker Hub...'
                    bat """
                    set DOCKER_REGISTRY_USER=%DOCKER_REGISTRY_USER%
                    docker compose pull
                    """

                    // Deploy and scale using the parameterized input
                    echo "Starting application services scaled to ${params.SCALE_COUNT} instances..."
                    bat """
                    set DOCKER_REGISTRY_USER=%DOCKER_REGISTRY_USER%
                    docker compose up -d --scale app=%SCALE_COUNT%
                    """

                    echo 'Verifying running containers...'
                    sleep(time: 5, unit: 'SECONDS')
                    bat """
                    docker ps
                    """
                }
            }
        }

        post {
            always {
                echo 'Logging out of Docker Hub...'
                bat '''
                docker logout
                '''
                cleanWs()
            }
            success {
                echo 'Deployment complete!'
            }
            failure {
                echo 'Pipeline failed. Check build logs for errors.'
            }
        }
    }
  ──