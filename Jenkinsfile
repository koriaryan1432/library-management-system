pipeline {
    agent any

    environment {
        // Replace with your Docker Hub username
        DOCKER_REGISTRY_USER = 'koriaryan'
        IMAGE_NAME           = 'library_app'
        IMAGE_TAG            = 'latest'
        
        // This ID corresponds to the Credentials ID configured in Jenkins (Username with password)
        DOCKER_HUB_CREDS     = credentials('docker-hub-credentials')
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
                sh "docker build -t ${DOCKER_REGISTRY_USER}/${IMAGE_NAME}:${IMAGE_TAG} ."
            }
        }

        stage('Push to Docker Hub') {
            steps {
                echo 'Logging in to Docker Hub and pushing image...'
                // Log in using the credentials retrieved via credentials helper
                sh "echo \$DOCKER_HUB_CREDS_PSW | docker login -u \$DOCKER_HUB_CREDS_USR --password-stdin"
                // Push the image
                sh "docker push ${DOCKER_REGISTRY_USER}/${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }

        stage('Deploy (Pull & Compose)') {
            steps {
                echo 'Stopping existing deployment...'
                // Export environment variable so docker-compose knows which image to pull
                sh "export DOCKER_REGISTRY_USER=${DOCKER_REGISTRY_USER} && docker compose down"

                echo 'Pulling fresh image from Docker Hub...'
                sh "export DOCKER_REGISTRY_USER=${DOCKER_REGISTRY_USER} && docker compose pull"

                echo 'Starting application services...'
                sh "export DOCKER_REGISTRY_USER=${DOCKER_REGISTRY_USER} && docker compose up -d"

                echo 'Verifying running containers...'
                sleep 5
                sh 'docker ps'
            }
        }
    }

    post {
        always {
            echo 'Logging out of Docker Hub...'
            sh 'docker logout'
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
