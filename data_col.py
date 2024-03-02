import cv2
import sys
import os
import time
import numpy as np

start = 0
start_flag = 1
i = 0

cwd = os.getcwd()

while(1):

	if(start_flag):
		start_flag = 0
		start = time.time()

	
	if not(np.round(time.time()-start) % 20):
		os.system('libcamera-still -t 100 -n -o train.jpg')
		frame = cv2.imread("train.jpg")[0:1232, 0:1640]
		traindir = cwd+"/training" + str(i) + ".jpg"
		cv2.imwrite(cwd+"/training/sample" + str(i) + ".jpg", frame)
		i += 1    
