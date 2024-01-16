import cv2
import RPi.GPIO as GPIO
import sys
import time
import numpy as np
from parameters import slope, intercept

# Eventually these will just be hard coded
slope = np.array(slope)
intercept = np.array(intercept)

vid1 = cv2.VideoCapture(1)
vid2 = cv2.VideoCapture(2)

left_done  = False
right_done = False

## GPIO Config. ## 
SOLENOID_IN = 11
LEFT_CNTRL  = 13
RIGHT_CTRL  = 15

GPIO.setmode(GPIO.BOARD) # uses pin numbers
GPIO.setup(SOLENOID_IN, GPIO.IN)
GPIO.setup(LEFT_CNTRL, GPIO.OUT)
GPIO.setup(RIGHT_CNTRL, GPIO.OUT)

GPIO.output(LEFT_CNTRL, GPIO.LOW)
GPIO.output(RIGHT_CNTRL, GPIO.LOW)
####

def crispiness_to_colour(crispiness):
    return np.multiply(crispiness, slope) + intercept
    
def expand_colour_range(colour, tolerance = 10):
    ranges = []
    for i in range(3):
        ranges.append([colour[i] - tolerance, colour[i] + tolerance])
    return ranges

def display_frame(frame1, frame2):
    # Mirror the frame (it just looks better but we can remove this later)
    frame1 = cv2.flip(frame1, 1)
    frame2 = cv2.flip(frame2, 1)

    # Display both frames side by side
    frame = np.hstack((frame1, frame2))
    cv2.imshow('frame', frame)

def toast_done_left():
    GPIO.output(LEFT_CNTRL, GPIO.LOW)
    print("Left Done!")

def toast_done_right():
    GPIO.output(RIGHT_CNTRL, GPIO.LOW)
    print("Right Done!")

def eject():
    print("Ejected!")

crispiness = float(sys.argv[1])

if(not(crispiness>=0 and crispiness<=1)):
    print("Invalid crispiness.")
    exit()

ranges = expand_colour_range(crispiness_to_colour(crispiness))
blue_range, green_range, red_range = ranges[0], ranges[1], ranges[2]
print("Target:\t\t", crispiness_to_colour(crispiness))

start_ctrl = 1
start_time = 0
durration = 0

while(True): 

    if not(GPIO.input(SOLENOID_IN)):

        if start_ctrl:
            start_time = time.time()
            start_ctrl = 0

        GPIO.output(LEFT_CNTRL, GPIO.HIGH)
        GPIO.output(RIGHT_CNTRL, GPIO.HIGH)
        time.sleep(0.5)
        # Capture the video frame by frame 
        ret1, frame1 = vid1.read()
        ret2, frame2 = vid2.read()

        # Get average colour of each frame
        average1 = np.array(cv2.mean(frame1)[0:3])
        average2 = np.array(cv2.mean(frame2)[0:3])

        display_frame(frame1, frame2)

        # Print both averages
        print("Left/Right:\t", average1, "/", average2, end='\r')

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

        if((time.time()-start_time)>150): #2.5 min until break (not forsure if this will stop the circuit may have to set gpio)
            break

        # Quit with 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

GPIO.cleanup()
vid1.release()
vid2.release()
cv2.destroyAllWindows()