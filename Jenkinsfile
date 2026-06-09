pipeline {
    agent any

    environment {
        // Docker Hub username
        DOCKER_REGISTRY_USER = 'koriaryan'
        IMAGE_NAME           = 'library_app'
        IMAGE_TAG            = 'latest'

        // Jenkins Credentials ID
        DOCKER_HUB_CREDS = credentials('docker-hub-creds')
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

        stage('Deploy (Pull & Compose)') {
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

                echo 'Starting application services...'

                bat """
                set DOCKER_REGISTRY_USER=%DOCKER_REGISTRY_USER%
                docker compose up -d
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