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
import enum
import datetime
from i2ctest import TCAM
from crisp_net import CrispClassifier
import sendImg
from PIL import Image
from io import BytesIO
from toasterHWI import ToasteHW
from time_remaining_estimate import get_new_time_remaining
#import gui.gui as gui
# import gui

HARDWARE_CONNECTED = False

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
target_crispiness = 0.5
abort_mode = 0

ble_service = None

# TODO: merge abort_state, and other state variables in to State enum
class State(str, enum.Enum):
    IDLE = 'IDLE'
    CONFIGURED = 'CONFIGURED'
    TOASTING = 'TOASTING'
    DONE = 'DONE'
    CANCELLED = 'CANCELLED'

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
    global abort_state, toaster, ble_service
    print("abort mode:",abort_mode)
    if abort_mode:
        print("Abort Initialized")
        toaster.emergencyEject()
        abort_state = True
        ble_service.set_state(State.IDLE)
    else:
        time.sleep(1)
        ab =toaster.getAbort()
        # gui.press(ab)

def solenoid_callBack(channel):
    global solTrigger
    toaster.setSolenoid(1)
    print("Slider down")
    solTrigger = 1

def gui_callBack(crisp_input):
    global target_crispiness, crisp_set
    if crisp_input is None:
        crisp_set = 0
        target_crispiness = 0.5
    else:
        target_crispiness = crisp_input/100
        crisp_set = 1
        print("crispiness target: ", target_crispiness)

def ble_cancel_callback():
    global abort_state, toaster, ble_service
    print("BLE Cancel Received")
    toaster.emergencyEject()
    abort_state = True
    ble_service.set_state(State.IDLE)

## SETUP ## 

if __name__ == '__main__':
    print("main 0")
    # BLE Startup
    ble_service = ble.init(gui_callBack,ble_cancel_callback)
    print("main 1")
    toaster = ToasteHW(abort_callBack,solenoid_callBack)
    signal.signal(signal.SIGINT, signal_handler)
    #gui.init (gui_callBack)
    print("main 2")
    if (HARDWARE_CONNECTED):
        # camera config
        cam1 = TCAM(0x55)#address of first esp unfortunatly hardcoded
        cam1.begin()
        print("main 3")
        # load trained model
        model = CrispClassifier()
        model.load()
    
    while(1): # multi cycle while loop
        print("\n\n\n Loop reset \n\n\n")
        ble_service.set_state(State.IDLE)
        abort_state = False
        solTrigger = 0
        print("waiting for sol")
        while(not solTrigger):
            time.sleep(0.01)
            if (not HARDWARE_CONNECTED):
                time.sleep(0.5) # temp
                x = input("Type to simulate solenoid lowered ") # Temp
                if x:
                    ble_service.set_state(State.CONFIGURED)
                    break
        solTrigger = 0
        abort_mode = 1
        while(not crisp_set):
           time.sleep(0.01)
        crip_set = 0
        abort_mode = 0
        print("Starting Cycle")
        time_left = get_new_time_remaining(0, target_crispiness)
        ble_service.set_time_remaining(time_left)
        ble_service.set_state(State.TOASTING)
        #gui.setState(1)
        if (HARDWARE_CONNECTED):
            cam1.requestPhoto()
            cam1.collect()
        # while(not crisp_set and not abort_state):
        #    time.sleep(0.1)
        # crisp_set = 0
        
        if(not abort_state):
            print("Crispiness:", target_crispiness)
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

                if (HARDWARE_CONNECTED):
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
                        
                        print("Target: ",target_crispiness)
                        print("Current Crispiness: ",left_crisp)
                        ble_service.set_current_crispiness(left_crisp) # send update to app
                        if(left_crisp>=target_crispiness and dt>10):
                            left_done = True
                        right_done = left_done

                        cur_pic = buff_len
                        print("Picture read: "+str(dt)+" Buffer length: "+str(buff_len))
                else:
                    # Testing without hardware
                    x = input("\nType to simulate cooking \n\n") # Temp
                    if x == '':
                        left_done = True
                        right_done = left_done
                    else:
                        left_crisp = float(x)

                    print("Target: ",target_crispiness)
                    print("Current Crispiness: ",left_crisp)
                    ble_service.set_current_crispiness(left_crisp) # send update to app
                    time_left = get_new_time_remaining(left_crisp, target_crispiness)
                    ble_service.set_time_remaining(time_left)

                    if (left_crisp >= target_crispiness):
                        print("Crispiness reached")
                        left_done = True
                        right_done = left_done

                time.sleep(1)
            except Exception as error:
                print(error)
                toaster.emergencyEject()
                abort_state=True
            
        if (HARDWARE_CONNECTED):
            sendImg.sendBuffers(buff,tbuff)
        cleanUp()
        toaster.eject()
        ble_service.set_state(State.DONE)
        # gui.setState(0)
        time.sleep(3)
        toaster.clearEject()
        
    GPIO.cleanup()
