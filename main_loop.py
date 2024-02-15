import cv2
import RPi.GPIO as GPIO
import sys
import os
import time
import numpy as np
from parameters import slope, intercept

MAX_TIME = 30
T_SAMPLE = 10
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

def toast_done_left():
    GPIO.output(LEFT_CNTRL, GPIO.LOW)
    print("Left Done!")

def toast_done_right():
    GPIO.output(RIGHT_CNTRL, GPIO.LOW)
    print("Right Done!")

def eject():
    GPIO.output(SOLENOID_OUT, GPIO.LOW)
    print("Ejected!")

crispiness = float(sys.argv[1])

if(not(0 <= crispiness <= 1)):
    print("Invalid crispiness.")
    GPIO.cleanup()
    exit()

ranges = expand_colour_range(crispiness_to_colour(crispiness))
blue_range, green_range, red_range = ranges[0], ranges[1], ranges[2]
print("Target:\t\t", crispiness_to_colour(crispiness))

start_ctrl = 1
start_time,dt = 0

while(True): 

    if not(GPIO.input(SOLENOID_IN)):

        if start_ctrl:
            start_time = time.time()
            start_ctrl = 0

        GPIO.output(LEFT_CNTRL, GPIO.HIGH)
        GPIO.output(RIGHT_CNTRL, GPIO.HIGH)
        time.sleep(0.5)


        if not(dt%T_SAMPLE):
            # Capture the video frame by frame 
            os.system('libcamera-still -t 100 -n -o test.jpg')
            # Get average colour of each frame
            frame = cv2.imread("test.jpg")
            average1 = np.array(cv2.mean(frame[0:1232, 0:1640])[0:3])
            average2 = np.array(cv2.mean(frame[1232:2464, 0:1640])[0:3])

            # Print both averages
            print("Left/Right:\t", average1, "/", average2, end='\r') #small left big right

            # Done if average colour is within a certain range
            if left_done == False and blue_range[0] < average1[0] < blue_range[1] and green_range[0] < average1[1] < green_range[1] and red_range[0] < average1[2] < red_range[1]:
                left_done = True
                toast_done_left()
            
            if right_done == False and blue_range[0] < average2[0] < blue_range[1] and green_range[0] < average2[1] < green_range[1] and red_range[0] < average2[2] < red_range[1]:
                right_done = True
                toast_done_right()

            if left_done and right_done:
                eject()
                break

        if(dt=(time.time()-start_time)>MAX_TIME): #2.5 min until break (not forsure if this will stop the circuit may have to set gpio)
            break

        # Quit with 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

GPIO.cleanup()
