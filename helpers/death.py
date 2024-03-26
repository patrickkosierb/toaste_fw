import RPi.GPIO as GPIO
import time 

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

GPIO.output(LEFT_CNTRL, GPIO.HIGH)
GPIO.output(RIGHT_CNTRL, GPIO.HIGH)
GPIO.output(SOLENOID_OUT, GPIO.HIGH)

time.sleep(180)

GPIO.output(LEFT_CNTRL, GPIO.LOW)
GPIO.output(RIGHT_CNTRL, GPIO.LOW)
GPIO.output(SOLENOID_OUT, GPIO.LOW)

GPIO.cleanup()
