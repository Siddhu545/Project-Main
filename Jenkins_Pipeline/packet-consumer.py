import threading
import numpy as np
import pandas as pd
import ipaddress
from sklearn.preprocessing import LabelEncoder
import joblib
from kafka import KafkaConsumer
from flask import Flask, jsonify
import json
import jenkins
import os
import time

# Load the trained model
model = joblib.load('./trained_model.pkl')

# Jenkins configuration (if needed)
jenkins_host = os.getenv('JENKINS_HOST', 'http://localhost:8080')
jenkins_username = os.getenv('JENKINS_USERNAME', '5id_K')
jenkins_password = os.getenv('JENKINS_PASSWORD', 'Siddhu@545')

# Initialize Jenkins server connection
jenkins_server = jenkins.Jenkins(jenkins_host, username=jenkins_username, password=jenkins_password)

# Flask app setup
app = Flask(__name__)

# Kafka configuration
kafka_bootstrap_servers = ['kafka:9093']
kafka_topic = 'network-packets-ids'
consumer = KafkaConsumer(kafka_topic,
                         bootstrap_servers=kafka_bootstrap_servers,
                         value_deserializer=lambda x: json.loads(x.decode('utf-8')))

# Global variable to hold packet information
packets = []

def ip_to_int(ip_str):
    return int(ipaddress.ip_address(ip_str))

def preprocess_packet(packet_info):
    df_packet = pd.DataFrame([packet_info])
    
    print("Original packet info:")
    print(df_packet)

    df_packet['source'] = df_packet['source'].apply(ip_to_int)
    df_packet['destination'] = df_packet['destination'].apply(ip_to_int)
    encoder = LabelEncoder()
    df_packet['sourceTCPFlagsDescription'] = encoder.fit_transform(df_packet['sourceTCPFlagsDescription'])
    df_packet['destinationTCPFlagsDescription'] = encoder.fit_transform(df_packet['destinationTCPFlagsDescription'])
    df_packet['protocolName'] = encoder.fit_transform(df_packet['protocolName'])
    df_packet['startDateTime'] = pd.to_datetime(df_packet['startDateTime'], format='%Y-%m-%dT%H:%M:%S.%f')
    df_packet['stopDateTime'] = pd.to_datetime(df_packet['stopDateTime'], format='%Y-%m-%dT%H:%M:%S.%f')

    df_packet['duration'] = (df_packet['stopDateTime'] - df_packet['startDateTime']).dt.total_seconds()
    df_packet.drop(['startDateTime', 'stopDateTime'], axis=1, inplace=True)
    
    print("Processed packet info:")
    print(df_packet.columns)
    
    return df_packet

def consume_messages():
    global packets
    for message in consumer:
        packet_info = message.value
        packets.append(packet_info)
        print(f"Received packet: {packet_info}")

def predict():
    if not packets:
        return jsonify({'error': 'No packets available for prediction'}), 400
    
    packet_info = packets.pop(0)
    df_packet = preprocess_packet(packet_info).values

    print("Packet ready for prediction:")
    print(df_packet)

    prediction = model.predict(df_packet)[0]
    label = 'anomaly' if prediction == 1 else 'normal'

    if label == 'anomaly':
        trigger_jenkins_job(label)

    return jsonify({'packet_info': packet_info, 'Label': label})

def trigger_jenkins_job(label):
    job_name = 'ids'
    parameters = {
        'label': label
    }
    try:
        jenkins_server.build_job(job_name, parameters)
        print(f"Triggered Jenkins job '{job_name}' with label '{label}'")
    except jenkins.JenkinsException as e:
        print(f"Failed to trigger Jenkins job: {e}")

@app.route('/predict', methods=['GET'])
def predict_route():
    return predict()

def start_flask():
    app.run(host='0.0.0.0', port=5002)

if __name__ == '__main__':
    threading.Thread(target=consume_messages, daemon=True).start()
    threading.Thread(target=start_flask, daemon=True).start()
