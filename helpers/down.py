import RPi.GPIO as GPIO
import time 

# ## GPIO Config. ## 
SOLENOID_IN = 26
SOLENOID_OUT  = 27
LEFT_CNTRL  = 22
RIGHT_CNTRL = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup(SOLENOID_IN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SOLENOID_OUT, GPIO.OUT)
GPIO.setup(LEFT_CNTRL, GPIO.OUT)
GPIO.setup(RIGHT_CNTRL, GPIO.OUT)

while True:

    while(GPIO.input(SOLENOID_IN)):
        time.sleep(0.1)

    GPIO.output(SOLENOID_OUT, GPIO.HIGH)
    GPIO.output(LEFT_CNTRL, GPIO.HIGH)
    GPIO.output(RIGHT_CNTRL, GPIO.HIGH)
    time.sleep(10)
    GPIO.output(SOLENOID_OUT, GPIO.LOW)
    GPIO.output(LEFT_CNTRL, GPIO.LOW)
    GPIO.output(RIGHT_CNTRL, GPIO.LOW)
    break
GPIO.cleanup()
#         time.sleep(30)

#         GPIO.output(LEFT_CNTRL, GPIO.LOW)
#         GPIO.output(RIGHT_CNTRL, GPIO.LOW)
#         GPIO.output(SOLENOID_OUT, GPIO.LOW)

#     GPIO.cleanup()

