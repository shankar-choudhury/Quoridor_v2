import time
import json
import paho.mqtt.client as mqtt

from lamp_quoridor_common import *
from quoridor_led import valid_move, players_turn, win_lose

FP_DIGITS = 2

MAX_STARTUP_WAIT_SECS = 10.0

MQTT_CLIENT_ID = "quoridor"

# Run in background of lampi with system service

class LampService(object):
    def __init__(self):
        self._client = self._create_and_configure_broker_client()

    def _create_and_configure_broker_client(self):
        client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=MQTT_VERSION)
        client.enable_logger()
        client.on_connect = self.on_connect
        client.message_callback_add(TOPIC_QUORIDOR_GAME,
                                    self.on_game_state)
        client.message_callback_add(TOPIC_QUORIDOR_MOVE,
                                    self.on_valid_move)
        client.message_callback_add(TOPIC_QUORIDOR_TURN,
                                    self.on_player_turn)
        client.on_message = self.default_on_message

        return client
    
    def serve(self):
        start_time = time.time()
        while True:
            try:
                self._client.connect(MQTT_BROKER_HOST,
                                     port=MQTT_BROKER_PORT,
                                     keepalive=MQTT_BROKER_KEEP_ALIVE_SECS)
                print("Connnected to broker")
                break
            except ConnectionRefusedError as e:
                current_time = time.time()
                delay = current_time - start_time
                if (delay) < MAX_STARTUP_WAIT_SECS:
                    print("Error connecting to broker; delaying and "
                          "will retry; delay={:.0f}".format(delay))
                    time.sleep(1)
                else:
                    raise e
        self._client.loop_forever()

    def on_connect(self, client, userdata, rc, unknown):
        self._client.subscribe(TOPIC_QUORIDOR_GAME, qos=1)
        self._client.subscribe(TOPIC_QUORIDOR_MOVE, qos=1)
        self._client.subscribe(TOPIC_QUORIDOR_TURN, qos=1)

    def on_valid_move(self, client, payload):
        is_valid = payload.<attribute>
        valid_move(is_valid)
    
    def on_player_turn(self, client, payload):
        is_players_turn = payload.<attribute>
        players_turn(is_players_turn)
    
    def on_game_state(self, client, payload):
        did_win = payload.<attribute>
        if did_win:
            win_lose(did_win)

    def default_on_message(self, client, msg):
        print("Received unexpected message on topic " +
              msg.topic + " with payload '" + str(msg.payload) + "'")
        
lamp = LampService()
lamp.serve()
