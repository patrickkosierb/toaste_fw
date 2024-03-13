import RPi.GPIO as GPIO
import time 
import signal

# GPIO.cleanup()

## GPIO Config. ## 
SOLENOID_IN = 26
ABORT_IN = 24
SOLENOID_OUT  = 27
LEFT_CNTRL  = 22
RIGHT_CNTRL = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup(SOLENOID_IN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ABORT_IN, GPIO.IN)

GPIO.setup(SOLENOID_OUT, GPIO.OUT)
GPIO.setup(LEFT_CNTRL, GPIO.OUT)
GPIO.setup(RIGHT_CNTRL, GPIO.OUT)

def signal_handle(sig, frame):
    print(sig)


def abort(channel):
    print("Abort Initialized")
    GPIO.output(LEFT_CNTRL, GPIO.LOW)
    GPIO.output(RIGHT_CNTRL, GPIO.LOW)
    GPIO.output(SOLENOID_OUT, GPIO.LOW)
    GPIO.cleanup()
    exit()

if __name__ == '__main__':
    GPIO.add_event_detect(ABORT_IN, GPIO.FALLING, callback=abort, bouncetime=100)
    signal.signal(signal.SIGINT,signal_handle)

    while 1:

        if not(GPIO.input(SOLENOID_IN)):
            GPIO.output(LEFT_CNTRL, GPIO.HIGH)
            GPIO.output(RIGHT_CNTRL, GPIO.HIGH)
            GPIO.output(SOLENOID_OUT, GPIO.HIGH)
        else:
            GPIO.output(LEFT_CNTRL, GPIO.LOW)
            GPIO.output(RIGHT_CNTRL, GPIO.LOW)
            GPIO.output(SOLENOID_OUT, GPIO.LOW)

        
    GPIO.cleanup()
