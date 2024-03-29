import cv2
import RPi.GPIO as GPIO
import sys
import os
import time
import numpy as np
import signal
from parameters import slope, intercept
import paho.mqtt.client as mqtt
import sys
import threading
import ble

cwd = os.getcwd()
## GPIO MACROS ## 
SOLENOID_IN = 26
ABORT_IN = 24
SOLENOID_OUT  = 27
LEFT_CNTRL  = 22
RIGHT_CNTRL = 23
 
## MQTT MACROS ## 
MQTT_ADDRESS = '172.20.10.4'
MQTT_USER = 'pi'
MQTT_PASSWORD = 'toast'
MQTT_TOPIC_PICTURE = 'picture'
MQTT_TOPIC = 'testing'

## OTHER ## 
MAX_TIME = 300  
T_SAMPLE = 10
ERROR_BOUND = 5
slope = np.array(slope)
intercept = np.array(intercept)
left_done  = False
right_done = False
pic_count = 1

def crispiness_to_colour(crispiness):
    return np.multiply(crispiness, slope) + intercept
    
def compare(state, current, final, bound, pin):
    error = np.linalg.norm(current-final)
    if state == False and error <= bound:
        GPIO.output(pin, GPIO.LOW)
        return True
    return state

def heaters(trigger):
    GPIO.output(LEFT_CNTRL,trigger)
    GPIO.output(RIGHT_CNTRL, trigger)

def eject():
    heaters(GPIO.LOW)
    GPIO.output(SOLENOID_OUT, GPIO.LOW)
    print("Ejected!")
    left_done = False
    right_done = False

## ABORT CALLBACKS ##
def signal_handler(sig, frame):
    print('SIGINT received. Exiting gracefully.')
    eject()
    GPIO.cleanup()
    exit()

def abort_button(channel):
    print("Abort Initialized")
    eject()
    GPIO.cleanup()
    exit()

## SETUP ##
def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SOLENOID_IN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ABORT_IN, GPIO.IN)
    GPIO.setup(SOLENOID_OUT, GPIO.OUT)
    GPIO.setup(LEFT_CNTRL, GPIO.OUT)
    GPIO.setup(RIGHT_CNTRL, GPIO.OUT)
    GPIO.output(LEFT_CNTRL, GPIO.LOW)
    GPIO.output(RIGHT_CNTRL, GPIO.LOW)
    GPIO.output(SOLENOID_OUT, GPIO.HIGH)
    GPIO.add_event_detect(ABORT_IN, GPIO.FALLING, callback=abort_button, bouncetime=100)
    signal.signal(signal.SIGINT, signal_handler)


def task_control(crispiness):
    global pic_count
    start_ctrl = 1
    start_time, dt = 0, 0

    if(not(0 <= crispiness <= 1)):
        print("Invalid crispiness.")
        GPIO.cleanup()
        exit()

    target = crispiness_to_colour(crispiness)
    print(crispiness)
    print("Target:\t\t", target)
    
    while(1): 
        if not(GPIO.input(SOLENOID_IN)) or True: #when the slider is down

            if start_ctrl: #timer 
                start_time = time.time()
                start_ctrl = 0
                heaters(GPIO.HIGH)
                time.sleep(0.5)

            dt = int(np.round(time.time()-start_time))

            if not(dt%T_SAMPLE) and dt>0:

                file = cwd+"/espData/"+str(pic_count-1)+".jpg"
                print("Reading Image", pic_count-1)
                frame = cv2.imread(file)
                left_avg = np.array(cv2.mean(frame)[0:3])
                print( "Left:\t", left_avg, "\n") 
                # left_done = compare(left_done, left_avg, target, ERROR_BOUND, LEFT_CNTRL)
                # right_done = compare(right_done, right_avg, target, ERROR_BOUND, RIGHT_CNTRL)
                right_done = True
                time.sleep(1)  
                
            if not(dt%5) and dt>0:
                # heaters(GPIO.LOW)
                # time.sleep(0.5)
                mqtt_client.publish(MQTT_TOPIC_PICTURE,1)
                # heaters(GPIO.HIGH)
                time.sleep(3) 

            if left_done and right_done or dt > MAX_TIME:
                eject()
                break   

    GPIO.cleanup()

def process_connect(client, userdata, flags, rc):
    print('Connected with result code ' + str(rc))
    client.subscribe(MQTT_TOPIC)

def process_message(client, userdata, msg):
    global pic_count 
    print("Received picture: ", pic_count)
    with open("espData/"+str(pic_count)+".jpg", "wb") as f:
        f.write(msg.payload)
        pic_count+=1
        f.close()

if __name__ == '__main__':

    setup()

    input = float(sys.argv[1])
    
    client_id = "process"
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = process_connect
    mqtt_client.on_message = process_message
    mqtt_client.max_packet_size = 20000
    mqtt_client.connect(MQTT_ADDRESS, 1883)
    

    app = ble.Application()
    ble_service = ble.ToastE_Service(0)
    app.add_service(ble_service)
    app.register()
    adv = ble.ToastE_Advertisement(0)
    adv.register()


    reader_thread = threading.Thread(target=ble.reader, args=(ble_service,))
    ble_thread = threading.Thread(target=ble.start_ble, args=(app,))
    # cntrl_thread = threading.Thread(target=task_control, name="Control Thread", args=(input,))
    
    # cntrl_thread.start()
    # mqtt_client.loop_forever()
    
    ble_thread.start()
    reader_thread.start()
    
    while(not ble_service.get_target_crispiness()):
        time.sleep(1)
    crisp = ble_service.get_target_crispiness()/100
    cntrl_thread = threading.Thread(target=task_control, name="Control Thread", args=(crisp,))
    cntrl_thread.start()  
    mqtt_client.loop_forever() 

    

