import paho.mqtt.publish as publish
import json
from django.conf import settings
from .models import Device

class QuoridorMQTTPublisher:
    @staticmethod
    def _get_device_topic(device, message_type):
        if not device or not device.device_id:
            raise ValueError("Invalid device")
        return f"{settings.MQTT_CONFIG['TOPIC_PREFIX']}{device.device_id}/{message_type}"

    @staticmethod
    def publish_turn(device, is_players_turn):
        publish.single(
            topic=QuoridorMQTTPublisher._get_device_topic(device, "turn"),
            payload=json.dumps({"is_players_turn": is_players_turn}),
            hostname=settings.MQTT_CONFIG['BROKER_HOST'],
            port=settings.MQTT_CONFIG['BROKER_PORT'],
            qos=1
        )

    @staticmethod
    def publish_move_validity(device, is_valid):
        publish.single(
            topic=QuoridorMQTTPublisher._get_device_topic(device, "move"),
            payload=json.dumps({"is_valid": is_valid}),
            hostname=settings.MQTT_CONFIG['BROKER_HOST'],
            port=settings.MQTT_CONFIG['BROKER_PORT'],
            qos=1
        )

    @staticmethod
    def publish_game_result(device, did_win):
        publish.single(
            topic=QuoridorMQTTPublisher._get_device_topic(device, "game"),
            payload=json.dumps({"did_win": did_win}),
            hostname=settings.MQTT_CONFIG['BROKER_HOST'],
            port=settings.MQTT_CONFIG['BROKER_PORT'],
            qos=1
        )