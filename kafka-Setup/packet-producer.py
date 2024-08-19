from flask import Flask, jsonify
from scapy.all import sniff, IP, TCP, UDP
from kafka import KafkaProducer
import json
from datetime import datetime
import requests
import threading
import time

app = Flask(__name__)

kafka_bootstrap_servers = ['kafka:9093']
kafka_topic = 'network-packets-ids'
producer = KafkaProducer(bootstrap_servers=kafka_bootstrap_servers,
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

totalSourceBytes = {}
totalDestinationBytes = {}
totalSourcePackets = {}
totalDestinationPackets = {}
sourceTCPFlagsDescription = {}
destinationTCPFlagsDescription = {}
startDateTime = None
stopDateTime = None

interface = input('Enter the network interface name: ')
capture_duration = int(input('Enter the capture duration (in seconds): '))

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
        ethertype = ip_layer.proto
        size = len(packet)
        ttl = ip_layer.ttl
        checksums = ip_layer.chksum
        flags = str(ip_layer.flags)
        
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
            duration = calculate_duration(startDateTime, stopDateTime)
        
        elif UDP in packet:
            udp_layer = packet[UDP]
            sourcePort = udp_layer.sport
            destinationPort = udp_layer.dport
            protocolName = "udp_ip"
            duration = calculate_duration(startDateTime, stopDateTime)

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

        return producer.send(kafka_topic, value=packet_info)

@app.route('/capture-packets', methods=['POST'])
def capture_packets():
    print(f'Starting packet capture on interface {interface} for {capture_duration} seconds...')
    sniff(iface=interface, prn=packet_handler, timeout=capture_duration)
    return jsonify({"status": "Packet capture completed"}), 200

def automate_capture():

    time.sleep(5)  
    requests.post('http://localhost:5001/capture-packets')
    print("Capture request sent.")

def start_flask():
    app.run(host='0.0.0.0', port=5001)

if __name__ == '__main__':

    threading.Thread(target=start_flask).start()


    automate_capture()
