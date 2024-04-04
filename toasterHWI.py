import RPi.GPIO as GPIO

## GPIO MACROS ## 
SOLENOID_IN = 26
ABORT_IN = 24
SOLENOID_OUT  = 27
LEFT_CNTRL  = 22
RIGHT_CNTRL = 23

class ToasteHW:
    def __init__(self,abortCB,solenoidCB):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SOLENOID_IN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(ABORT_IN, GPIO.IN,pull_up_down=GPIO.PUD_UP)
        GPIO.setup(SOLENOID_OUT, GPIO.OUT)
        GPIO.setup(LEFT_CNTRL, GPIO.OUT)
        GPIO.setup(RIGHT_CNTRL, GPIO.OUT)
        GPIO.output(LEFT_CNTRL, GPIO.LOW)
        GPIO.output(RIGHT_CNTRL, GPIO.LOW)
        GPIO.output(SOLENOID_OUT, GPIO.LOW)
        GPIO.add_event_detect(ABORT_IN, GPIO.FALLING, callback=abortCB, bouncetime=100)
        GPIO.add_event_detect(SOLENOID_IN, GPIO.FALLING, callback=solenoidCB, bouncetime=100)
        self.emergency_eject_state=0

    def setLeft(self,sig):
        if(sig == 1 and self.emergency_eject_state == 0):
            GPIO.output(LEFT_CNTRL, GPIO.HIGH)
        else:
            GPIO.output(LEFT_CNTRL, GPIO.LOW)
            
    def setRight(self,sig):
        if(sig == 1 and self.emergency_eject_state == 0):
            GPIO.output(RIGHT_CNTRL, GPIO.HIGH)
        else:
            GPIO.output(RIGHT_CNTRL, GPIO.LOW)

    def setSolenoid(self,sig):
        if(sig == 1 and self.emergency_eject_state == 0):
            GPIO.output(SOLENOID_OUT, GPIO.HIGH)
        else:
            GPIO.output(SOLENOID_OUT, GPIO.LOW)
        
    def eject(self):
        GPIO.output(RIGHT_CNTRL, GPIO.LOW)
        GPIO.output(LEFT_CNTRL, GPIO.LOW)
        GPIO.output(SOLENOID_OUT, GPIO.LOW)
        print("Normal Ejected!")

    def emergencyEject(self):
        self.emergency_eject_state = 1
        GPIO.output(RIGHT_CNTRL, GPIO.LOW)
        GPIO.output(LEFT_CNTRL, GPIO.LOW)
        GPIO.output(SOLENOID_OUT, GPIO.LOW)
        print("Emergency Ejected!")

    def clearEject(self):
        self.emergency_eject_state = 0