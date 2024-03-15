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

## OTHER ## 
MAX_TIME = 300
T_SAMPLE = 10
ERROR_BOUND = 5
slope = np.array(slope)
intercept = np.array(intercept)
left_done  = False
right_done = False

def mqtt():
    client_id = "main"
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.connect(MQTT_ADDRESS, 1883)

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

def abort(channel):
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

    GPIO.add_event_detect(ABORT_IN, GPIO.FALLING, callback=abort, bouncetime=100)
    signal.signal(signal.SIGINT, signal_handler)

    mqtt()

if __name__ == '__main__':

    setup()

    crispiness = float(sys.argv[1])
    if(not(0 <= crispiness <= 1)):
        print("Invalid crispiness.")
        GPIO.cleanup()
        exit()

    target = crispiness_to_colour(crispiness)
    
    print("Target:\t\t", target)

    start_ctrl = 1
    start_time, dt = 0, 0

    captureCount = len(os.listdir("/espData"))
    while(True): 
        # Have BLE Waiting for crispiness here once we test this 

        if not(GPIO.input(SOLENOID_IN)): #when the slider is down

            if start_ctrl: #timer 
                start_time = time.time()
                start_ctrl = 0
                heaters(GPIO.HIGH)
                time.sleep(0.5)

            dt = np.round(time.time()-start_time)

            if not(dt % T_SAMPLE):
                
                heaters(GPIO.LOW)
    
                mqtt_client.publish(MQTT_TOPIC_PICTURE,1); 
                time.sleep(0.5)

                heaters(GPIO.HIGH)
                frame = cv2.imread((os.listdir("/espData")[-1]))
                
                
                left_avg = np.array(cv2.mean(frame)[0:3])
                
                print("SETPOINT ::",target, "\n Left:\t", left_avg, end='\r') 

                left_done = compare(left_done, left_avg, target, ERROR_BOUND, LEFT_CNTRL)
                # right_done = compare(right_done, right_avg, target, ERROR_BOUND, RIGHT_CNTRL)
                right_done = True  
                    
                if left_done and right_done or dt > MAX_TIME:
                    eject()
                    break                    

    GPIO.cleanup()
