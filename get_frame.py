import paho.mqtt.client as mqtt

MQTT_ADDRESS = '172.20.10.4'
MQTT_USER = 'pi'
MQTT_PASSWORD = 'toast'
MQTT_TOPIC = 'left'


def on_connect(client, userdata, flags, rc):
    """ The callback for when the client receives a CONNACK response from the server."""
    print('Connected with result code ' + str(rc))
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    """The callback for when a PUBLISH message is received from the server."""
    print(msg.topic + ' ' + str(msg.payload))

if __name__ == '__main__':
    client_id = "pipub"
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect(MQTT_ADDRESS, 1883)
    mqtt_client.loop_forever()