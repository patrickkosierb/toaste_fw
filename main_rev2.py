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
from toasterHWI import ToasteHW
#import gui.gui as gui
import gui

cwd = os.getcwd()

toaster = None
## OTHER ## 
MAX_TIME = 420
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
abort_state = False
solTrigger = 0
crisp_set = 0
crispiness = 0.5
abort_mode = 0

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

def cleanUp():
    global left_done, right_done, pic_count, buff, tbuff
    left_done = False
    right_done = False
    pic_count = 0
    buff = []
    tbuff = []


## ABORT CALLBACKS ##
def signal_handler(sig, frame):
    print('SIGINT received. Exiting gracefully.')
    toaster.emergencyEject()
    time.sleep(0.5); #delay for slider
    GPIO.cleanup()
    exit()

def abort_callBack(channel):
    global abort_state, toaster
    print("abort mode:",abort_mode)
    if abort_mode:
        print("Abort Initialized")
        toaster.emergencyEject()
        abort_state = True
    else:
        time.sleep(1)
        ab =toaster.getAbort()
        gui.press(ab)
    

def solenoid_callBack(channel):
    global solTrigger
    toaster.setSolenoid(1)
    print("Slider down")
    solTrigger = 1

def gui_callBack(crisp):
    global crispiness, crisp_set
    crispiness = crisp/100
    crisp_set = 1

## SETUP ## 

if __name__ == '__main__':
    print("main 1")
    toaster = ToasteHW(abort_callBack,solenoid_callBack)
    signal.signal(signal.SIGINT, signal_handler)
    #gui.init (gui_callBack)
    print("main 2")
    # camera config
    cam1 = TCAM(0x55)#address of first esp unfortunatly hardcoded
    cam1.begin()
    print("main 3")
    # load trained model
    model = CrispClassifier()
    model.load()
    
    while(1): # multi cycle while loop
        abort_state = False
        solTrigger = 0
        print("waiting for sol")
        while(not solTrigger):
            time.sleep(0.01)
        solTrigger = 0
        abort_mode = 1
        #while(not crisp_set):
        #    time.sleep(0.01)
        crip_set = 0
        abort_mode = 0
        print("Starting Cycle")
        #gui.setState(1)
        cam1.requestPhoto()
        cam1.collect()
        #while(not crisp_set and not abort_state):
        #    time.sleep(0.1)
        #crisp_set = 0
        
        if(not abort_state):
            print("Crispiness:", crispiness)
            start_ctrl = 1
            start_time = time.time()
            toaster.setLeft(1)
            toaster.setRight(1)
            time.sleep(0.5)
            cur_pic = 0

        dt = 0
        while(dt<MAX_TIME and not (left_done and right_done) and not abort_state):
            try:
                dt = int(np.round(time.time()-start_time))

                if not(dt%T_SAMPLE): #take picture
                    #toaster.setLeft(0)
                    #toaster.setRight(0)
                    toaster.setLED(1)
                    time.sleep(0.6)
                    ret = cam1.requestPhoto()
                    time.sleep(0.3)
                    toaster.setLED(0)
                    #toaster.setLeft(1)
                    #toaster.setRight(1)
                    if(ret):
                        ret = cam1.collect()
                        if(ret):
                            buff.append(cam1.getCurrentBuff())
                            tbuff.append(dt)
                            cam1.saveCurrentBuff()

                buff_len = len(buff)
                if buff_len > cur_pic: #read picture

                    # process buffer for cnn input 
                    img = Image.open(BytesIO(bytearray(buff[buff_len-1])))
                    left_crisp = model.predictCrispiness(img)
                    print("Target: ",cripsiness)
                    print("Current Crispiness: ",left_crisp)
                    if(left_crisp>=target and dt>10):
                        left_done = True
                    right_done = left_done

                    cur_pic = buff_len
                    print("Picture read: "+str(dt)+" Buffer length: "+str(buff_len))

                time.sleep(1)
            except Exception as error:
                print(error)
                toaster.emergencyEject()
                abort_state=True
            
        sendImg.sendBuffers(buff,tbuff)
        cleanUp()
        toaster.eject()
        gui.setState(0)
        time.sleep(3)
        toaster.clearEject()
        
    GPIO.cleanup()
