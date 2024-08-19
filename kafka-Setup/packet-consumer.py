import threading
import numpy as np
import pandas as pd
import ipaddress
from sklearn.preprocessing import LabelEncoder
import joblib
from kafka import KafkaConsumer
from flask import Flask, jsonify
import json

model = joblib.load('/app/trained_model.pkl')

app = Flask(__name__)

kafka_bootstrap_servers = ['kafka:9093']
kafka_topic = 'network-packets-ids'
consumer = KafkaConsumer(kafka_topic,
                         bootstrap_servers=kafka_bootstrap_servers,
                         value_deserializer=lambda x: json.loads(x.decode('utf-8')))

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

@app.route('/predict', methods=['POST'])
def predict():
    packet_labels = []

    for message in consumer:
        packet_info = message.value

        df_packet = preprocess_packet(packet_info).values

        print("Packet ready for prediction:")
        print(df_packet)

        prediction = model.predict(df_packet)[0]
        label = 'anomaly' if prediction == 1 else 'normal'

        packet_labels.append({'packet_info': packet_info, 'Label': label})

    return jsonify(packet_labels)

def automate_prediction():
    print("Starting prediction automatically...")
    predict()

if __name__ == '__main__':

    threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 5002}).start()


    automate_prediction()
