import paho.mqtt.client as mqtt_client
import json
from django.conf import settings
from .models import Device
import threading

class QuoridorMQTTPublisher:
    _client = None
    _lock = threading.Lock()
    _connected = False

    @classmethod
    def _get_client(cls):
        if cls._client is None:
            with cls._lock:
                if cls._client is None:
                    cls._client = mqtt_client.Client()
                    cls._client.on_connect = cls._on_connect
                    try:
                        cls._client.connect(
                            settings.MQTT_CONFIG['BROKER_HOST'],
                            port=settings.MQTT_CONFIG['BROKER_PORT']
                        )
                        cls._client.loop_start()
                    except Exception as e:
                        print(f"MQTT connection error: {e}")
        return cls._client
    
    @classmethod
    def _on_connect(cls, client, userdata, flags, rc):
        cls._connected = True
        print("MQTT Connected")

    @staticmethod
    def _get_device_topic(device, message_type):
        if not device or not device.device_id:
            raise ValueError("Invalid device")
        return f"{settings.MQTT_CONFIG['TOPIC_PREFIX']}{device.device_id}/{message_type}"

    @staticmethod
    def publish_turn(device, is_players_turn):
        try:
            client = QuoridorMQTTPublisher._get_client()
            if client and QuoridorMQTTPublisher._connected:
                client.publish(
                    topic=QuoridorMQTTPublisher._get_device_topic(device, "turn"),
                    payload=json.dumps({"is_players_turn": is_players_turn}),
                    qos=1
                )
        except Exception as e:
            print(f"MQTT publish error: {e}")

    @staticmethod
    def publish_move_validity(device, is_valid):
        try:
            client = QuoridorMQTTPublisher._get_client()
            if client and QuoridorMQTTPublisher._connected:
                client.publish(
                    topic=QuoridorMQTTPublisher._get_device_topic(device, "move"),
                    payload=json.dumps({"is_valid": is_valid}),
                    qos=1
                )
        except Exception as e:
            print(f"MQTT publish error: {e}")

    @staticmethod
    def publish_game_result(device, did_win):
        try:
            client = QuoridorMQTTPublisher._get_client()
            if client and QuoridorMQTTPublisher._connected:
                client.publish(
                    topic=QuoridorMQTTPublisher._get_device_topic(device, "game"),
                    payload=json.dumps({"did_win": did_win}),
                    qos=1
                )
        except Exception as e:
            print(f"MQTT publish error: {e}")