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
MAX_TIME = 120  
T_SAMPLE = 10
ERROR_BOUND = 5
slope = np.array(slope)
intercept = np.array(intercept)

left_done  = False
right_done = False

pic_count = 1
buff = []
abort_butt = False

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
    buff = []


## ABORT CALLBACKS ##
def signal_handler(sig, frame):
    print('SIGINT received. Exiting gracefully.')
    eject()
    GPIO.cleanup()
    exit()

def abort_button(channel):
    print("Abort Initialized")
    global abort_butt
    abort_butt = True
    # eject()
    # GPIO.cleanup()
    # exit()

def process_connect(client, userdata, flags, rc):
    print('Connected with result code ' + str(rc))
    client.subscribe(MQTT_TOPIC)

def process_message(client, userdata, msg):
    global pic_count 
    print("Received picture: ", pic_count)
    buff.append(msg.payload)
    with open("espData/"+str(pic_count)+".jpg", "wb") as f:
        f.write(msg.payload)
        pic_count+=1
        f.close()

def mqtt_task(client):
    client.loop_forever() 

## SETUP ##
def gpio_setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SOLENOID_IN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ABORT_IN, GPIO.IN)
    GPIO.setup(SOLENOID_OUT, GPIO.OUT)
    GPIO.setup(LEFT_CNTRL, GPIO.OUT)
    GPIO.setup(RIGHT_CNTRL, GPIO.OUT)
    GPIO.output(LEFT_CNTRL, GPIO.LOW)
    GPIO.output(RIGHT_CNTRL, GPIO.LOW)
    GPIO.output(SOLENOID_OUT, GPIO.LOW)
    GPIO.add_event_detect(ABORT_IN, GPIO.FALLING, callback=abort_button, bouncetime=100)
    signal.signal(signal.SIGINT, signal_handler)


if __name__ == '__main__':
    
    gpio_setup()

    # MQTT Startup
    client_id = "process"
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = process_connect
    mqtt_client.on_message = process_message
    mqtt_client.max_packet_size = 20000
    mqtt_client.connect(MQTT_ADDRESS, 1883)

    # BLE Startup
    # app = ble.Application()
    # ble_service = ble.ToastE_Service(0)
    # app.add_service(ble_service)
    # app.register()
    # adv = ble.ToastE_Advertisement(0)
    # adv.register()

    # reader_thread = threading.Thread(target=ble.reader, args=(ble_service,))
    # ble_thread = threading.Thread(target=ble.start_ble, args=(app,))
    mqtt_thread = threading.Thread(target=mqtt_task, args=(mqtt_client,))

    mqtt_thread.start()
    # ble_thread.start()
    # reader_thread.start()

    # ble_service.set_state(ble.State.IDLE)

    crispiness = float(sys.argv[1])


    if(not(0 <= crispiness <= 1)):
        print("Invalid crispiness.")
        GPIO.cleanup()
        exit()

    # target = crispiness_to_colour(crispiness)
    # ranges = expand_colour_range(target)
    # blue_range, green_range, red_range = ranges[0], ranges[1], ranges[2]
    # print("Target:\t\t", crispiness_to_colour(crispiness))

    while(1): # multi cycle while loop

        abort_butt = False
        while(GPIO.input(SOLENOID_IN)):
            time.sleep(0.1)

        GPIO.output(SOLENOID_OUT, GPIO.HIGH)
        
        #TODO: take base picture 
        print("Slider down")

        if(GPIO.input(SOLENOID_IN)):
            abort_butt = True
        
        # while(not ble_service.get_target_crispiness() and not abort_butt):
        #     time.sleep(0.1)
        
        # dtCrisp = 0
        # startCrisp = time.time()
        # pastC = ble_service.get_target_crispiness()

        # while(dtCrisp<=5 and not abort_butt):
        #     dtCrisp = int(np.round(time.time()-startCrisp))
        #     cur = ble_service.get_target_crispiness()
            
        #     if((abs(cur-pastC)>=5)):
        #         startCrisp = time.time()
        #         pastC = cur
        #     time.sleep(1)

        # ble_service.set_state(ble.State.TOASTING)

        if(not abort_butt):
            # crispiness = ble_service.get_target_crispiness()/100
            print("Crispiness input"+str(crispiness))
            target = crispiness_to_colour(crispiness)
            print("Target:\t\t", target)

            start_ctrl = 1
            dt = 0
            start_time = time.time()
            heaters(GPIO.HIGH)
            time.sleep(0.5)
            cur_pic = 0
            # ble_service.set_state(ble.State.TOASTING)

        while(dt<MAX_TIME and not (left_done and right_done) and not abort_butt):

            dt = int(np.round(time.time()-start_time))

            if not(dt%T_SAMPLE): #take picture
                heaters(GPIO.LOW)
                time.sleep(0.5)
                mqtt_client.publish(MQTT_TOPIC_PICTURE,1)
                heaters(GPIO.HIGH)
                # time.sleep(3) 

            buff_len = len(buff)

            if buff_len > cur_pic: #read picture
                nparr = np.frombuffer(buff[buff_len-1], np.uint8)
                img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR) # cv2.IMREAD_COLOR in OpenCV 3.1
                left_avg = np.array(cv2.mean(img_np)[0:3])

                print( "Left:\t", left_avg, "\n") 
                # left_done = compare(left_done, left_avg, target, ERROR_BOUND, LEFT_CNTRL)
                # right_done = left_done
                # right_done = compare(right_done, right_avg, target, ERROR_BOUND, RIGHT_CNTRL)
                cur_pic = buff_len
                print("Picture read: "+str(dt)+" Buffer length: "+str(buff_len))
            
            time.sleep(1) 

        eject()
        # ble_service.set_state(ble.State.IDLE)  
        time.sleep(2)
    GPIO.cleanup()