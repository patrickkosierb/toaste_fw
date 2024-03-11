import paho.mqtt.client as mqtt
from PIL import Image
import io
import base64
import time
# to start broker
# sudo mosquitto -c /etc/mosquitto/mosquitto.conf

MQTT_ADDRESS = '172.20.10.4'
MQTT_USER = 'pi'
MQTT_PASSWORD = 'toast'
MQTT_TOPIC = 'testing'
MQTT_TOPIC_START = 'start'


def on_connect(client, userdata, flags, rc):
    print('Connected with result code ' + str(rc))
    client.subscribe(MQTT_TOPIC)
    # client.subscribe(MQTT_TOPIC_START)

def on_message(client, userdata, msg):
    # pix = msg.payload.decode('utf-8')
    print(msg.payload)

if __name__ == '__main__':
    client_id = "pipub"
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.max_packet_size = 500

    mqtt_client.connect(MQTT_ADDRESS, 1883)

    mqtt_client.loop_forever()

    