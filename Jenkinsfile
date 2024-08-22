pipeline {
    agent any

    environment {
        KAFKA_DOCKER_IMAGE = 'confluentinc/cp-kafka:latest'
        KAFKA_CONTAINER_NAME = 'kafka'
        GIT_REPO_URL = 'https://github.com/Siddhu545/Project-Main.git'
        GIT_BRANCH = 'main'
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: "${GIT_BRANCH}", url: "${GIT_REPO_URL}"
            }
        }

        stage('Setup-Python') {
            steps {
                script {
                    sh 'docker pull python:3.9-slim'
                }
            }
        }

        stage ('Setup Virtual Env for Python') {
            steps {
                script {
                    sh '''
                        if [ -d "venv" ]; then
                            echo "Siddhu@545" | sudo -S rm -rf venv
                        fi
                        sudo python3 -m venv venv
                        . venv/bin/activate
                        cd Jenkins_Pipeline
                    '''
                }
            }
        }

        stage('Pull Kafka Image') {
            steps {
                script {
                    sh 'docker pull ${KAFKA_DOCKER_IMAGE}'
                }
            }
        }

        stage('Setup Kafka') {
            steps {
                script {
                    sh '''
                        docker run -d \
                            --name ${KAFKA_CONTAINER_NAME} \
                            -p 9093:9093 \
                            -e KAFKA_ADVERTISED_LISTENERS=INSIDE://localhost:9093,OUTSIDE://localhost:9092 \
                            -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=INSIDE:PLAINTEXT,OUTSIDE:PLAINTEXT \
                            -e KAFKA_LISTENERS=INSIDE://0.0.0.0:9093,OUTSIDE://0.0.0.0:9092 \
                            -e KAFKA_LISTENER_NAME_PLAINTEXT=INSIDE \
                            -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 \
                            ${KAFKA_DOCKER_IMAGE}
                    '''
                }
            }
        }

        stage('Run Packet Capture and Prediction') {
            steps {
                script {
                    // Run the Flask app for packet capture and prediction
                    sh '''
                        . venv/bin/activate
                        cd Jenkins_Pipeline
                        python3 packet-producer.py > capture.log 2>&1 &
                        python3 packet-consumer.py > prediction.log 2>&1 &
                    '''
                }
            }
        }

        stage('View Logs') {
            steps {
                script {
                    sh '''
                        echo "----- Capture Log -----"
                        cat capture.log
                        echo "----- Prediction Log -----"
                        cat prediction.log
                    '''
                }
            }
        }
    }

    post {
        always {
            sh '''
                docker stop ${KAFKA_CONTAINER_NAME} || true
                docker rm ${KAFKA_CONTAINER_NAME} || true
                docker system prune -f
            '''
        }
    }
}
