import paho.mqtt.client as mqtt
import sys

MQTT_ADDRESS = '172.20.10.4'
MQTT_USER = 'pi'
MQTT_PASSWORD = 'toast'
MQTT_TOPIC_START = 'picture'


if __name__ == '__main__':

    cntrl = sys.argv[1]

    client_id = "pipub2"
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

    mqtt_client.connect(MQTT_ADDRESS, 1883)
    mqtt_client.publish(MQTT_TOPIC_START,cntrl); 

    

