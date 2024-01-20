import cv2
import RPi.GPIO as GPIO
import sys
import os
import time
import numpy as np
import logging
from parameters import slope, intercept

MAX_TIME = 30
## GPIO Config. ## 
SOLENOID_IN = 26
SOLENOID_OUT  = 27
LEFT_CNTRL  = 22
RIGHT_CNTRL = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup(SOLENOID_IN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SOLENOID_OUT, GPIO.OUT)
GPIO.setup(LEFT_CNTRL, GPIO.OUT)
GPIO.setup(RIGHT_CNTRL, GPIO.OUT)

GPIO.output(LEFT_CNTRL, GPIO.LOW)
GPIO.output(RIGHT_CNTRL, GPIO.LOW)
GPIO.output(SOLENOID_OUT, GPIO.HIGH)

slope = np.array(slope)
intercept = np.array(intercept)
left_done, right_done  = False
start_flag = 1
start_time, dt = 0

def crispiness_to_colour(crispiness):
    return np.multiply(crispiness, slope) + intercept
    
def expand_colour_range(colour, tolerance = 20):
    ranges = []
    for i in range(3):
        ranges.append([colour[i] - tolerance, colour[i] + tolerance])
    return ranges

def compare(state, color_current, blue, green, red, gpio_pin):
    if state == False and blue[0] < color_current[0] < blue[1] and green[0] < color_current[1] < green[1] and red[0] < color_current[2] < red[1]:
        GPIO.output(gpio_pin, GPIO.LOW)
        logging.info(str(gpio_pin)+" Done!") #this is cursed
        return True 
    return state

def control_task():
    return 0

def server_task():
    return 0

logging.basicConfig(level=logging.INFO,format="%(asctime)s [%(levelname)s] %(message)s",handlers=[logging.FileHandler("cntrl_log.log"),logging.StreamHandler()])

crispiness = float(sys.argv[1])

if(not(0 <= crispiness <= 1)):
    logging.info("Invalid crispiness.")
    GPIO.cleanup()
    exit()

ranges = expand_colour_range(crispiness_to_colour(crispiness))
blue_range, green_range, red_range = ranges[0], ranges[1], ranges[2]
logging.info("Target:\t\t", crispiness_to_colour(crispiness))

while(True): 

    if not(GPIO.input(SOLENOID_IN)):

        if start_flag:
            # get crispiness from app here break if there is an error or poll for some time
            start_time = time.time()
            start_flag = 0

        GPIO.output(LEFT_CNTRL, GPIO.HIGH)
        GPIO.output(RIGHT_CNTRL, GPIO.HIGH)
        time.sleep(0.5)

        if not(dt%10):
            # Capture the video frame by frame 
            os.system('libcamera-still -t 100 -n -o test.jpg')
            
            frame = cv2.imread("test.jpg")
            left_avg = np.array(cv2.mean(frame[0:1232, 0:1640])[0:3])
            right_avg = np.array(cv2.mean(frame[1232:2464, 0:1640])[0:3])
           
            logging.info("Left/Right:\t", left_avg, "/", right_avg, end='\r') #small left big right

            left_done  = compare(left_done, left_avg, blue_range, green_range, red_range, LEFT_CNTRL)
            right_done = compare(right_done, right_avg, blue_range, green_range, red_range, RIGHT_CNTRL)

            if left_done and right_done:
                GPIO.output(SOLENOID_OUT, GPIO.LOW)
                break

        if(dt=time.time()-start_time>MAX_TIME): 
            break
        
        # Quit with 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

GPIO.cleanup()


