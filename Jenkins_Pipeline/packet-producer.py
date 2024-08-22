from flask import Flask, request, jsonify, render_template
from scapy.all import sniff, IP, TCP, UDP
from kafka import KafkaProducer
import json
from datetime import datetime
import threading
import time
import requests
import jenkins
import os

# Jenkins configuration
host = os.getenv('JENKINS_HOST', 'http://localhost:8080')
username = os.getenv('JENKINS_USERNAME', '5id_K')
password = os.getenv('JENKINS_PASSWORD', 'Siddhu@545')

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# Kafka configuration
kafka_bootstrap_servers = ['kafka:9093']
kafka_topic = 'network-packets-ids'
producer = KafkaProducer(
    bootstrap_servers=kafka_bootstrap_servers,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Global variables for packet statistics
totalSourceBytes = {}
totalDestinationBytes = {}
totalSourcePackets = {}
totalDestinationPackets = {}
sourceTCPFlagsDescription = {}
destinationTCPFlagsDescription = {}
startDateTime = None
stopDateTime = None

def get_flag_description(flags):
    flag_descriptions = {
        'F': 'FIN',
        'S': 'SYN',
        'R': 'RST',
        'P': 'PSH',
        'A': 'ACK',
        'U': 'URG',
        'E': 'ECE',
        'C': 'CWR'
    }
    return ''.join(flag_descriptions.get(flag, '') for flag in flags)

def calculate_duration(start, stop):
    start_time = datetime.fromisoformat(start)
    stop_time = datetime.fromisoformat(stop)
    duration = stop_time - start_time
    return duration.total_seconds()

def packet_handler(packet):
    global startDateTime, stopDateTime
    
    if startDateTime is None:
        startDateTime = datetime.now().isoformat()

    stopDateTime = datetime.now().isoformat()

    if IP in packet:
        ip_layer = packet[IP]
        src = ip_layer.src
        dst = ip_layer.dst
        size = len(packet)
        
        totalSourceBytes[src] = totalSourceBytes.get(src, 0) + size
        totalDestinationBytes[dst] = totalDestinationBytes.get(dst, 0) + size
        totalSourcePackets[src] = totalSourcePackets.get(src, 0) + 1
        totalDestinationPackets[dst] = totalDestinationPackets.get(dst, 0) + 1
        
        sourcePort = None
        destinationPort = None
        protocolName = None
        duration = calculate_duration(startDateTime, stopDateTime)
        
        if TCP in packet:
            tcp_layer = packet[TCP]
            sourcePort = tcp_layer.sport
            destinationPort = tcp_layer.dport
            protocolName = "tcp_ip"
            sourceTCPFlagsDescription[src] = get_flag_description(str(tcp_layer.flags))
            destinationTCPFlagsDescription[dst] = get_flag_description(str(tcp_layer.flags))
        
        elif UDP in packet:
            udp_layer = packet[UDP]
            sourcePort = udp_layer.sport
            destinationPort = udp_layer.dport
            protocolName = "udp_ip"

        packet_info = {
            "totalSourceBytes": totalSourceBytes[src],
            "totalDestinationBytes": totalDestinationBytes[dst],
            "totalSourcePackets": totalSourcePackets[src],
            "totalDestinationPackets": totalDestinationPackets[dst],
            "sourceTCPFlagsDescription": sourceTCPFlagsDescription.get(src),
            "destinationTCPFlagsDescription": destinationTCPFlagsDescription.get(dst),
            "source": src,
            "protocolName": protocolName,
            "destination": dst,
            "sourcePort": sourcePort,
            "destinationPort": destinationPort,
            "startDateTime": startDateTime,
            "stopDateTime": stopDateTime,
            "duration": duration,
        }

        print(json.dumps(packet_info, indent=4))

        producer.send(kafka_topic, value=packet_info)

@app.route('/capture-packets', methods=['POST'])
def capture_packets():
    interface = request.form.get('interface')
    duration = int(request.form.get('duration'))
    
    if not interface or not duration:
        return jsonify({"error": "Missing interface or duration"}), 400
    
    try:
        server = jenkins.Jenkins(host, username=username, password=password)
        print('Connected to Jenkins')
        
        # Trigger Jenkins job with parameters
        server.build_job('ids/main', parameters={
            'interface': interface,
            'duration': duration
        })
        return jsonify({"status": "Packet capture job started"}), 200
    except jenkins.JenkinsException as e:
        print(f'Error connecting to Jenkins: {e}')
        return jsonify({"error": "Failed to connect to Jenkins"}), 500

def automate_capture():
    time.sleep(5)  
    requests.post('http://localhost:5001/capture-packets')
    print("Capture request sent.")

def start_flask():
    app.run(host='0.0.0.0', port=5001)

if __name__ == '__main__':
    threading.Thread(target=start_flask).start()
    automate_capture()
