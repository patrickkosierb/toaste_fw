import cv2
import RPi.GPIO as GPIO
import sys
import os
import time
import numpy as np

start = 0
start_flag = 1
i = 0

while(1):

	if(start_flag):
		start_flag = 0
		start = time.time()

	if(time.time()-start % 10):

		os.system('libcamera-still -t 100 -n -o train.jpg')
		frame = cv2.imread("train.jpg")[0:1232, 0:1640]
		cv2.imwrite("training" + str(i) + ".jpg", frame)
		i += 1    
