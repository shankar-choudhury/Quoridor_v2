import time
import json
import paho.mqtt.client as mqtt

from lamp_quoridor_common import *
from quoridor_led import valid_move, players_turn, win_lose

FP_DIGITS = 2

MAX_STARTUP_WAIT_SECS = 10.0

MQTT_CLIENT_ID = "quoridor"

# Run in background of lampi with system service

class LampService:
    def __init__(self):
        self._client = self._create_and_configure_broker_client()

    def _create_and_configure_broker_client(self):
        client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=MQTT_VERSION)
        client.on_connect = self.on_connect
        client.message_callback_add(TOPIC_QUORIDOR_MOVE, self.on_valid_move)
        client.message_callback_add(TOPIC_QUORIDOR_TURN, self.on_player_turn)
        client.message_callback_add(TOPIC_QUORIDOR_GAME, self.on_game_state)
        client.on_message = self.default_on_message
        return client

    def serve(self):
        try:
            self._client.connect(
                MQTT_BROKER_HOST,
                port=MQTT_BROKER_PORT,
                keepalive=MQTT_BROKER_KEEP_ALIVE_SECS
            )
            print("Connected to broker")
            self._client.loop_forever()
        except KeyboardInterrupt:
            self._client.disconnect()
            print("Disconnected gracefully")

    def on_connect(self, client, userdata, flags, rc):
        client.subscribe([(TOPIC_QUORIDOR_MOVE, 1),
                         (TOPIC_QUORIDOR_TURN, 1),
                         (TOPIC_QUORIDOR_GAME, 1)])

    def on_valid_move(self, client, userdata, msg):
        payload = json.loads(msg.payload.decode())
        valid_move(payload["is_valid"])

    def on_player_turn(self, client, userdata, msg):
        payload = json.loads(msg.payload.decode())
        players_turn(payload["is_players_turn"])

    def on_game_state(self, client, userdata, msg):
        payload = json.loads(msg.payload.decode())
        win_lose(payload["did_win"])

    def default_on_message(self, client, userdata, msg):
        print(f"Unexpected message on {msg.topic}: {msg.payload.decode()}")

if __name__ == "__main__":
    LampService().serve()
