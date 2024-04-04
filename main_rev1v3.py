import cv2
import RPi.GPIO as GPIO
import sys
import os
import time
import numpy as np
import signal
from parameters import slope, intercept # TODO: Remove after cnn works
import sys
import threading
import ble
import datetime
from i2ctest import TCAM
from crisp_net import CrispClassifier
import sendImg
from PIL import Image
from io import BytesIO

cwd = os.getcwd()

## GPIO MACROS ## 
SOLENOID_IN = 26
ABORT_IN = 24
SOLENOID_OUT  = 27
LEFT_CNTRL  = 22
RIGHT_CNTRL = 23

## OTHER ## 
MAX_TIME = 300  
T_SAMPLE = 10
ERROR_BOUND = 5

# TODO: Remove after cnn works
slope = np.array(slope)
intercept = np.array(intercept)

left_done  = False
right_done = False
cam1=None
pic_count = 1
buff = []
tbuff = []
abort_butt = False

#### TODO: Remove after cnn works ####
def crispiness_to_colour(crispiness):
    return np.multiply(crispiness, slope) + intercept
    
def compare(state, current, final, bound, pin):
    error = np.linalg.norm(current-final)
    if state == False and error <= bound:
        GPIO.output(pin, GPIO.LOW)
        return True
    return state
#####################################

def heaters(trigger):
    GPIO.output(LEFT_CNTRL,trigger)
    GPIO.output(RIGHT_CNTRL, trigger)

def eject():
    global pic_count
    heaters(GPIO.LOW)
    GPIO.output(SOLENOID_OUT, GPIO.LOW)
    print("Ejected!")
    left_done = False
    right_done = False
    pic_count = 0
    buff = []
    tbuff = []

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

## SETUP ##
def gpio_setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SOLENOID_IN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ABORT_IN, GPIO.IN,pull_up_down=GPIO.PUD_UP)
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

    # BLE Startup
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
    ble_service.set_state(ble.State.IDLE)

    # camera config
    cam1 = TCAM(0x55)#address of first esp unfortunatly hardcoded
    cam1.begin()

    # load trained model
    #model = CrispClassifier()
    #model.load()
    
    while(1): # multi cycle while loop

        abort_butt = False
        while(GPIO.input(SOLENOID_IN)):
            time.sleep(0.1)

        GPIO.output(SOLENOID_OUT, GPIO.HIGH)
        time.sleep(0.1)
        #TODO: take base picture 
        print("Slider down")
        if(GPIO.input(SOLENOID_IN)):
            abort_butt = True
        
        #TODO: fix ble
        # while(not ble_service.get_target_crispiness() and not abort_butt):
        #     time.sleep(0.1)
                
        if(not abort_butt):
            # crispiness = ble_service.get_target_crispiness()/100 #get selected crispiness from ble module
            # print("Crispiness input"+str(crispiness)) 
            crispiness = 0.5 #hard coded for now
            target = crispiness_to_colour(crispiness)
            print("Target:\t\t", target)
            start_ctrl = 1
            start_time = time.time()
            heaters(GPIO.HIGH)
            time.sleep(0.5)
            cur_pic = 0
            ble_service.set_state(ble.State.TOASTING)

        dt = 0
        while(dt<MAX_TIME and not (left_done and right_done) and not abort_butt):
            try:
                dt = int(np.round(time.time()-start_time))

                if not(dt%T_SAMPLE): #take picture
                    heaters(GPIO.LOW)
                    time.sleep(0.5)
                    ret = cam1.requestPhoto()
                    heaters(GPIO.HIGH)
                    if(ret):
                        ret = cam1.collect()
                        if(ret):
                            buff.append(cam1.getCurrentBuff())
                            tbuff.append(dt)
                            cam1.saveCurrentBuff()

                buff_len = len(buff)
                if buff_len > cur_pic: #read picture

                    # process buffer for cnn input 
                    # img = Image.open(BytesIO(buff[buff_len-1]))
                    # left_crisp = model.predictCrispiness(img)
                    # print("Left Crispiness: ",left_crisp)
                    # if(left_crisp>=target):
                        # left_done = True
                    # right_done = left_done

                    ########### TODO: remove after cnn works ###########
                    #nparr = np.frombuffer(buff[buff_len-1], np.uint8)
                    #img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR) # cv2.IMREAD_COLOR in OpenCV 3.1
                    #left_avg = np.array(cv2.mean(img_np)[0:3])
                    # print( "Left:\t", left_avg, "\n") 
                    # left_done = compare(left_done, left_avg, target, ERROR_BOUND, LEFT_CNTRL)
                    # right_done = left_done
                    # right_done = compare(right_done, right_avg, target, ERROR_BOUND, RIGHT_CNTRL)
                    ####################################################
                    
                    cur_pic = buff_len
                    print("Picture read: "+str(dt)+" Buffer length: "+str(buff_len))
                time.sleep(1)
            except Exception as error:
                print(error)
                abort_butt=True
            
        sendImg.sendBuffers(buff,tbuff)
        eject()
        ble_service.set_state(ble.State.IDLE)  
        time.sleep(2)
        
    GPIO.cleanup()
