import paho.mqtt.client

DEVICE_ID_FILENAME = '/sys/class/net/eth0/address'

# MQTT Topic Names
TOPIC_QUORIDOR_GAME = "quoridor/game"
TOPIC_QUORIDOR_MOVE = "quoridor/move"
TOPIC_QUORIDOR_TURN = "quoridor/turn"

# MQTT Broker Connection info
MQTT_VERSION = paho.mqtt.client.MQTTv311
MQTT_BROKER_HOST = "192.168.1.94"
MQTT_BROKER_PORT = 1883
MQTT_BROKER_KEEP_ALIVE_SECS = 60

def get_device_id():
    mac_addr = open(DEVICE_ID_FILENAME).read().strip()
    return mac_addr.replace(':', '')