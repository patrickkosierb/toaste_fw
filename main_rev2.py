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
import time_remaining_estimate
#import gui.gui as gui
import gui

HARDWARE_CONNECTED = False # TODO: set manual for now, is there a way to make this automatic?

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
target_crispiness = 0.3
abort_mode = 0

ble_service = None

# TODO: merge abort_state, and other state variables into State enum?
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
    global abort_state, toaster, abort_mode, ble_service
    print("abort mode:",abort_mode)
    if abort_mode == 0:
        print("Abort Initialized")
        toaster.emergencyEject()
        abort_state = True
        ble_service.set_state(State.IDLE)
    else:
        time.sleep(1)
        ab =toaster.getAbort()
        if (HARDWARE_CONNECTED):
            gui.press(ab)


def solenoid_callBack(channel):
    global solTrigger
    toaster.setSolenoid(1)
    solTrigger = 1
    print("Slider down")

def gui_callBack(crisp_input):
    global target_crispiness, crisp_set
    if crisp_input is None:
        crisp_set = 0
        target_crispiness = 0.3
    else: #from old callback 
        target_crispiness = crisp_input/100
        crisp_set = 1
        print("crispiness target: ", target_crispiness)

def ble_cancel_callback():
    global abort_state, toaster, ble_service
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
    print("main 2")
    
    if (HARDWARE_CONNECTED):
        # camera config
        cam1 = TCAM(0x55)#address of first esp unfortunatly hardcoded

        print("main 3")
        # load trained model
        model = CrispClassifier()
        model.load()
        gui.init(gui_callBack)
    # timer thread setup with ble callback
    time_remaining_estimate.init(ble_service.set_time_remaining)
    
    while(1): # multi cycle while loop
        ble_service.set_state(State.IDLE)
        abort_state = False
        solTrigger = 0

        print("\n\nNew cycle!\nwaiting for sol")
        
        gui.setState(0)
        time.sleep(0.5)
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
        gui.setState(1)
        abort_mode = 1

        print("waiting input")
        time.sleep(1)
        cam1.begin()
        
        while(not crisp_set):
            time.sleep(0.01)
            
        crisp_set = 0
        gui.setState(2)
        time.sleep(4)
        abort_mode = 0
        print("Starting Cycle")
        cam1.requestPhoto()
        cam1.collect()
        
        time_remaining_estimate.calculate_new_time_estimate(0, target_crispiness)
        ble_service.set_state(State.TOASTING)
        #while(not crisp_set and not abort_state):
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
                ble_service.set_time_elapsed(dt)

                if (HARDWARE_CONNECTED):
                    if not(dt%T_SAMPLE): #take picture
                        
                        toaster.setLED(1)
                        time.sleep(0.6)
                        ret = cam1.requestPhoto()
                        time.sleep(0.3)
                        toaster.setLED(0)

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
                        time_remaining_estimate.calculate_new_time_estimate(left_crisp, target_crispiness)

                        if(left_crisp>=target_crispiness and dt>10):
                            left_done = True
                        right_done = left_done

                        cur_pic = buff_len
                        print("Picture read: "+str(dt)+" Buffer length: "+str(buff_len))
                else:
                    left_crisp = 0
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
                    time_remaining_estimate.calculate_new_time_estimate(left_crisp, target_crispiness)

                    if (left_crisp >= target_crispiness):
                        print("Crispiness reached")
                        left_done = True
                        right_done = left_done

                time.sleep(1)
            except Exception as error:
                print(error)
                toaster.emergencyEject()
                abort_state=True
                ble_service.set_state(State.CANCELLED) # can we hold this state longer? so app holds done screen longer.

            
        if (HARDWARE_CONNECTED):
            sendImg.sendBuffers(buff,tbuff)
        cleanUp()
        toaster.eject()
        ble_service.set_state(State.DONE) # can we hold this state longer? so app holds done screen longer.
        if (HARDWARE_CONNECTED):
            gui.setState(0)
        time.sleep(3)
        toaster.clearEject()
        
    GPIO.cleanup()
