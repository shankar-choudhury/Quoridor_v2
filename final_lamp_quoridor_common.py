import paho.mqtt.client

DEVICE_ID_FILENAME = '/sys/class/net/eth0/address'

def get_device_id():
    with open(DEVICE_ID_FILENAME) as f:
        mac_addr = f.read().strip()
    return mac_addr.replace(':', '')


# MQTT Topic Names
DEVICE_ID = get_device_id()
TOPIC_BASE = f"quoridor/device/{DEVICE_ID}"
TOPIC_QUORIDOR_GAME = f"{TOPIC_BASE}/game"
TOPIC_QUORIDOR_MOVE = f"{TOPIC_BASE}/move"
TOPIC_QUORIDOR_TURN = f"{TOPIC_BASE}/turn"

# MQTT Broker Connection info
MQTT_VERSION = paho.mqtt.client.MQTTv311
MQTT_BROKER_HOST = "ec2-34-192-115-190.compute-1.amazonaws.com"
MQTT_BROKER_PORT = 1883
MQTT_BROKER_KEEP_ALIVE_SECS = 60
