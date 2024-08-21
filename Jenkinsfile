pipeline {
    agent {
        docker {
            image 'python:3.9-slim'
            args '-u root'
        }
    }

    environment {
        KAFKA_DOCKER_IMAGE = 'confluentinc/cp-kafka:latest'
        KAFKA_CONTAINER_NAME = 'kafka'
        GIT_REPO_URL = 'https://github.com/Siddhu545/Project-Main.git'
        GIT_BRANCH = 'main'
    }

    stages {
        stage('Checkout') {
            steps {
                // Checkout the latest code from the repository
                git branch: "${GIT_BRANCH}", url: "${GIT_REPO_URL}"
            }
        }

        stage('Pull Kafka Image') {
            steps {
                script {
                    sh 'docker pull ${KAFKA_DOCKER_IMAGE}'
                }
            }
        }

        stage('Setup Kafka and Zookeeper') {
            steps {
                script {
                    // Run Kafka and Zookeeper in Docker containers
                    sh '''
                        docker network create kafka-net || true
                        docker run -d --name zookeeper --network kafka-net -p 2181:2181 confluentinc/cp-zookeeper:latest
                        
                        docker run -d --name ${KAFKA_CONTAINER_NAME} --network kafka-net \
                            -p 9093:9093 -p 9092:9092 \
                            -e KAFKA_BROKER_ID=1 \
                            -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 \
                            -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
                            ${KAFKA_DOCKER_IMAGE}
                    '''
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    // Install dependencies for your Flask apps
                    sh 'pip install -r Jenkins_Pipeline/requirements.txt'
                }
            }
        }

        stage('Run Packet Capture and Prediction') {
            steps {
                script {
                    // Run the packet capture and prediction scripts
                    sh '''
                        # Start the Flask app for packet capture
                        nohup python Jenkins_Pipeline/packet-producer.py > capture.log 2>&1 &

                        # Start the Flask app for prediction
                        nohup python Jenkins_Pipeline/packet-consumer.py > prediction.log 2>&1 &
                    '''
                }
            }
        }
    }

    post {
        always {
            // Clean up Docker containers after build
            sh '''
                docker stop ${KAFKA_CONTAINER_NAME} || true
                docker stop zookeeper || true
                docker rm ${KAFKA_CONTAINER_NAME} || true
                docker rm zookeeper || true
                docker network rm kafka-net || true
                docker system prune -f
            '''
        }
    }
}
