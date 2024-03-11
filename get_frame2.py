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
MQTT_TOPIC = 'left'

frame = []
count = 0
start = False
def on_connect(client, userdata, flags, rc):
    global count
    """ The callback for when the client receives a CONNACK response from the server."""
    count = 0
    print('Connected with result code ' + str(rc))
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    """The callback for when a PUBLISH message is received from the server."""
    global frame
    global count
    global start
    pix = msg.payload.decode('utf-8')
    print(msg.payload)
    if(pix == "ACK" ):
        start = time.time()
        frame = []
        print("caputre start")
    elif(pix == "FIN"):
        
        print("caputre done")
        intf = [int(x) for x in frame]
        intf = bytes(intf)
        img = Image.open(io.BytesIO(intf))
        img.save("capture"+str(count)+".jpg")
        end = time.time()
        count+=1
        print(start-end)
    else:
        frame.append(pix)

if __name__ == '__main__':
    client_id = "pipub"
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect(MQTT_ADDRESS, 1883)
    mqtt_client.loop_forever()