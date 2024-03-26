import cv2
import RPi.GPIO as GPIO
import sys
import os
import time
import numpy as np
import signal
from parameters import slope, intercept
import sys
import threading
import re
import ble

cwd = os.getcwd()
## GPIO MACROS ## 
SOLENOID_IN = 26
ABORT_IN = 24
SOLENOID_OUT  = 27
LEFT_CNTRL  = 22
RIGHT_CNTRL = 23

## OTHER ## 
MAX_TIME = 30
T_SAMPLE = 10
ERROR_BOUND = 5
slope = np.array(slope)
intercept = np.array(intercept)
left_done  = False
right_done = False

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
    global left_done
    global right_avg
    pic_count =0
    start_ctrl = 1
    start_time, dt = 0, 0

    if(not(0 <= crispiness <= 1)):
        print("Invalid crispiness.")
        GPIO.cleanup()
        exit()

    target = crispiness_to_colour(crispiness)
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

                heaters(GPIO.LOW)
                os.system('libcamera-still -t 100 -n -o '+cwd+'/arduData/capture'+str(pic_count)+'.jpg')
                heaters(GPIO.HIGH)

                frame = cv2.imread(cwd+"/arduData/capture"+str(pic_count)+".jpg")
                left_avg = np.array(cv2.mean(frame[0:1232, 0:1640])[0:3])
                print("Target:\n", target)
                print( "Left:\t", left_avg, "\n") 

                # left_done = compare(left_done, left_avg, target, ERROR_BOUND, LEFT_CNTRL)
                # right_done = compare(right_done, right_avg, target, ERROR_BOUND, RIGHT_CNTRL)
                right_done = True
                pic_count+=1

            if left_done and right_done or dt > MAX_TIME:
                eject()
                break   

    # GPIO.cleanup()


if __name__ == '__main__':

    setup()

    # input = float(sys.argv[1])
    
    app = ble.Application()
    ble_service = ble.ToastE_Service(0)
    app.add_service(ble_service)
    app.register()
    adv = ble.ToastE_Advertisement(0)
    adv.register()
    
    reader_thread = threading.Thread(target=ble.reader, args=(ble_service,))
    ble_thread = threading.Thread(target=ble.start_ble, args=(app,))
    
    ble_thread.start()
    reader_thread.start()
    
    while(not ble_service.get_target_crispiness()):
        time.sleep(1)
    crisp = ble_service.get_target_crispiness()/100
    print(crisp)
    cntrl_thread = threading.Thread(target=task_control, name="Control Thread", args=(crisp,))
    cntrl_thread.start()     

    # while(1):
    #     threads_list = threading.enumerate()
    #     lastThread = threads_list[-1].getName()
    #     print(lastThread)
    #     if(ble_service.get_target_crispiness() and lastThread != "Control Thread"):
    #         crisp = ble_service.get_target_crispiness()/100
    #         print(crisp)
    #         cntrl_thread = threading.Thread(target=task_control, name="Control Thread", args=(crisp,))
    #         cntrl_thread.start()


   
    
