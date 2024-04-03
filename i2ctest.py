from smbus2 import SMBus, i2c_msg
import time
import datetime
import math
import cv2
import numpy as np
import sys
import os

class TCAM:
	

	def __init__(self, address=0x55):
		self._picLen = 65538
		self._address = address
		self._state = True
		self._readMsg = None #= #i2c_msg.read(self._address,self._picLen)
		self._buff  = []
  	
	def begin(self):
		# Open I2C bus
		self._bus = SMBus(1,force=True)
		# Make sure we have the right device
		ret = False
		if(self.ping()):
			ret = self.config()
		time.sleep(0.1)
		print(ret)
		return ret
		
	def ping(self):
		data = bytes('p', 'utf-8')
		msg = i2c_msg.write(self._address,data)
		try:
			self._bus.i2c_rdwr(msg)
			return True
		except:
			return False
	
	def config(self):
		confbuff= []
		confbuff.append(ord('c'))
		confbuff.append(3)#s->set_quality //        0-63
		confbuff.append(2)##s->set_contrast//int   0 to 4
		confbuff.append(2)##s->set_brightness//int 0 to 4
		confbuff.append(2)##s->set_saturation//int  0 to 4
		confbuff.append(2)##s->set_sharpness//int   0 to 4
		confbuff.append(0)##s->set_denoise
		confbuff.append(0)##s->set_gainceiling     0-6
		confbuff.append(0)##s->set_colorbar
		confbuff.append(1)##s->set_whitebal    0 = disable , 1 = enable
		confbuff.append(1)##s->set_gain_ctrl
		confbuff.append(1)##s->set_exposure_ctrl
		confbuff.append(0)##s->set_hmirror
		confbuff.append(0)##s->set_vflip
		confbuff.append(0)##s->set_aec2
		confbuff.append(1)##s->set_awb_gain
		confbuff.append(0)##s->set_agc_gain         0 to 30
		confbuff.append(2)##s->set_ae_level//int   0 to 4
		confbuff.append(75)##s->set_aec_value//int16  0 to 256 *5
		confbuff.append(0)##s->set_special_effect  0 to 6 (0 - No Effect, 1 - Negative, 2 - Grayscale, 3 - Red Tint, 4 - Green Tint, 5 - Blue Tint, 6 - Sepia)
		confbuff.append(0)##s->set_wb_mode       0 to 4 - if awb_gain enabled (0 - Auto, 1 - Sunny, 2 - Cloudy, 3 - Office, 4 - Home)
		confbuff.append(1)##s->set_dcw
		confbuff.append(0)##s->set_bpc
		confbuff.append(1)##s->set_wpc
		confbuff.append(1)##s->set_raw_gma
		confbuff.append(0)##s->set_lenc
		data = bytearray(confbuff)
		write = i2c_msg.write(self._address,data)
		try:
			self._bus.i2c_rdwr(write)
			return True
		except:
			return False
			
	def requestPhoto(self):
		self._buff=[]
		data = bytes('r', 'utf-8')
		write = i2c_msg.write(self._address,data)
		try:
			self._bus.i2c_rdwr(write)
		except:
			return False
		time.sleep(0.1)
		return True

	def getPhoto(self):
		self._readMsg = i2c_msg.read(self._address,4)
		try:
			self._bus.i2c_rdwr(self._readMsg)
			time.sleep(0.01)
		except:
			return False
		block =[]
		for value in self._readMsg:
			block.append(value)
		testv = int.from_bytes(bytearray(block[0:3]),"little")
		print("i2count "+str(testv))
		
		self._readMsg = i2c_msg.read(self._address,12)
		try:
			self._bus.i2c_rdwr(self._readMsg)
			time.sleep(0.01)
		except:
			return False
		block= self._readMsg.buf[0:3]
		print(block)
		leng = int.from_bytes(block,"little")
		self._picLen = leng
		print("length "+str(leng))
		print(bytearray(list(self._readMsg)).hex())
		for i in range(math.ceil(leng/32)):
			self._readMsg = i2c_msg.read(self._address,32)
			try:
				self._bus.i2c_rdwr(self._readMsg)
				time.sleep(0.001)
				self._buff.extend(list(self._readMsg))
			except:
				return False
		return True

	def getCurrentBuff(self):
		return self._buff[0:self._picLen]
		
	def saveCurrentBuff(self):
		time = datetime.datetime.now().strftime("%m:%d:%Y,%H:%M:%S")
		with open("storedPics/"+time+"-"+"pic"+str(22)+".jpg", "wb") as f:
			f.write(bytearray(self._buff[0:self._picLen]))
			f.close()	
	
#cam1 = TCAM(0x55)
#cam1.begin()
#time.sleep(1)
#cam1.requestPhoto()
#cam1.getCurrentBuff()
