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
                // Checkout the latest code from the repository
                git branch: "${GIT_BRANCH}", url: "${GIT_REPO_URL}"
            }
        }

        stage('pull kafka image') {
            steps{
                script{
                    sh 'docker pull ${KAFKA_DOCKER_IMAGE}'
                }
            }
        }

        stage('Setup-Python') {
            steps {
                script {
                    sh 'docker pull python:3.9-slim'
                }
            }
        }

        stage('Setup Kafka') {
            steps {
                script {
                    // Run Kafka in a Docker container
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

        stage ('setup virtual env for python'){
            steps {
                script{
                    sh ''' 
                        # Check if the 'venv' directory exists
                        if [ -d "venv" ]; then
                        # If it exists, remove the directory
                        echo "Siddhu@545" | sudo -S rm -rf venv
                        fi

                        # Create the 'venv' directory
                        echo "Siddhu@545" | sudo -S mkdir venv

                        # Change permissions for the 'venv' directory
                        sudo chmod -R a+rwx venv

                        # Go into the 'venv' directory
                        cd venv 

                        # Create a virtual environment
                        sudo python3 -m venv .

                        # Activate the virtual environment
                        . bin/activate

                        # Install dependencies from the requirements file
                        python3 -m pip install -r ./requirements.txt
                    '''
                }
            }
        }

        stage('Run Packet Capture and Prediction') {
            steps {
                script {
                    // Run the packet capture and prediction scripts
                    sh '''
                        # Start the Flask app for packet capture
                        nohup python ../Jenkins_Pipeline/packet-producer.py > capture.log 2>&1 &
                        
                        # Start the Flask app for prediction
                        nohup python ../Jenkins_Pipeline/packet-consumer.py > prediction.log 2>&1 &
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
                docker rm ${KAFKA_CONTAINER_NAME} || true
                docker system prune -f
            '''
        }
    }
}
