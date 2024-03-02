import cv2
import RPi.GPIO as GPIO
import sys
import os
import time
import numpy as np
from parameters import slope, intercept

MAX_TIME = 300
T_SAMPLE = 10
ERROR_BOUND = 5
# Eventually these will just be hard coded
slope = np.array(slope)
intercept = np.array(intercept)

left_done  = False
right_done = False

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
#### 

def crispiness_to_colour(crispiness):
    return np.multiply(crispiness, slope) + intercept
    
def expand_colour_range(colour, tolerance = 20):
    ranges = []
    for i in range(3):
        ranges.append([colour[i] - tolerance, colour[i] + tolerance])
    return ranges

def eject():
    GPIO.output(SOLENOID_OUT, GPIO.LOW)
    print("Ejected!")
    
def compare(state, color_current, blue, green, red, gpio_pin):
    if state == False and blue[0] < color_current[0] < blue[1] and green[0] < color_current[1] < green[1] and red[0] < color_current[2] < red[1]:
        GPIO.output(gpio_pin, GPIO.LOW)
        return True 
    return state

def compare2(state, current, final, bound, pin):
    error = np.linalg.norm(current-final)
    if state == False and error <= bound:
        GPIO.output(pin, GPIO.LOW)
        return True
    return state

crispiness = float(sys.argv[1])

if(not(0 <= crispiness <= 1)):
    print("Invalid crispiness.")
    GPIO.cleanup()
    exit()

target = crispiness_to_colour(crispiness)

ranges = expand_colour_range(target)

blue_range, green_range, red_range = ranges[0], ranges[1], ranges[2]
print("Target:\t\t", crispiness_to_colour(crispiness))

start_ctrl = 1
start_time, dt = 0, 0

while(True): 

    if not(GPIO.input(SOLENOID_IN)):

        if start_ctrl:
            start_time = time.time()
            start_ctrl = 0

        GPIO.output(LEFT_CNTRL, GPIO.HIGH)
        GPIO.output(RIGHT_CNTRL, GPIO.HIGH)
        time.sleep(0.5)

        dt = np.round(time.time()-start_time)

        if not(dt % T_SAMPLE):
            # Capture the video frame by frame 
            os.system('libcamera-still -t 100 -n -o capture.jpg')
            # Get average colour of each frame
            frame = cv2.imread("capture.jpg")
            left_avg = np.array(cv2.mean(frame[0:1232, 0:1640])[0:3])
            right_avg = np.array(cv2.mean(frame[1232:2464, 0:1640])[0:3])

            # Print both averages
            print("Left/Right:\t", left_avg, "/", right_avg, end='\r') #small left big right

            # Done if average colour is within a certain range
            
            # left_done = compare(left_done, left_avg, blue_range, green_range, red_range, LEFT_CNTRL)
            # right_done = compare(right_done, right_avg, blue_range, green_range, red_range, RIGHT_CNTRL)

            left_done = compare2(left_done, left_avg, target, ERROR_BOUND, LEFT_CNTRL)
            # right_done = compare2(right_done, right_avg, target, ERROR_BOUND, RIGHT_CNTRL)
            right_done = True  
                
            if left_done and right_done or dt > MAX_TIME:
                eject()
                break

        # Quit with 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

GPIO.cleanup()
