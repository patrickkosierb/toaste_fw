from smbus2 import SMBus, i2c_msg
import time
import datetime
import math
import cv2
import numpy as np
import sys
import os
import crcengine

class TCAM:
	

	def __init__(self, address=0x55):
		self._picLen = 65538
		self._address = address
		self._state = True
		self._readMsg = None #= #i2c_msg.read(self._address,self._picLen)
		self._buff  = []
		self._failSleepTime = 1
		self._dt = 0.0001
		self._hash = crcengine.create_from_params(crcengine.CrcParams(0x07, 8, 0, reflect_in=True, reflect_out=True, xor_out=0))
  	
	def begin(self):
		# Open I2C bus
		self._bus = SMBus(1,force=True)
		# Make sure we have the right device
		ret = False
		if(self.ping()):
			ret = self.config()
			pass
		time.sleep(1)
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
		confbuff.append(12)#s->set_quality //        0-63
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
			print("error in config")
			return False
			
	def requestPhoto(self):
		self._buff=[]
		data = bytes('r', 'utf-8')
		write = i2c_msg.write(self._address,data)
		try:
			self._bus.i2c_rdwr(write)
		except Exception as error:
			print("err in req")
			print(error)
			print("sleeping it off")
			time.sleep(self._failSleepTime)
			return False
		time.sleep(0.01)
		return True

	def getPhoto(self):
		self._readMsg = i2c_msg.read(self._address,4+1)
		try:
			self._bus.i2c_rdwr(self._readMsg)
			time.sleep(self._dt)
		except Exception as error:
			print("err in init pull")
			print(error)
			print("sleeping it off")
			time.sleep(self._failSleepTime)
			return False
		block =[]
		for value in self._readMsg:
			block.append(value)
		testv = int.from_bytes(bytearray(block[0:3]),"little")
		#print("i2count "+str(testv))
		
		self._readMsg = i2c_msg.read(self._address,13+1)
		try:
			self._bus.i2c_rdwr(self._readMsg)
			time.sleep(self._dt)
		except Exception as error:
			print("err in length pull")
			print(error)
			print("sleeping it off")
			time.sleep(self._failSleepTime)
			return False
		block= self._readMsg.buf[1:4]
		#print(block)
		leng = int.from_bytes(block,"little")
		self._picLen = leng
		if(int.from_bytes(self._readMsg.buf[0],"little") != 0):
			print("Capture Failed")
		#print("length "+str(leng))
		#print(bytearray(list(self._readMsg)).hex())
		#print(bytearray(list(self._readMsg)[0:13]).hex())
		#print("crc")
		lcrca = int.from_bytes(self._readMsg.buf[13],"little")
		#print("digest")
		lcrcb = self._hash(bytearray(list(self._readMsg)[0:13]))
		if(lcrca != lcrcb):
			print("error in length")
			print("sleeping it off")
			time.sleep(self._failSleepTime)
			return False
		#print("Runs "+str(math.ceil(leng/31)))
		#print("start transfer")
		crcerr = False
		for i in range(math.ceil(leng/31)):
			getb = 31
			if((leng - i*31)<31):
				getb = leng - i*31
			#print(str(leng - i*31)+" " + str(getb))
			self._readMsg = i2c_msg.read(self._address,getb+1)
			try:
				self._bus.i2c_rdwr(self._readMsg)
				time.sleep(self._dt)
				self._buff.extend(list(self._readMsg)[0:getb])
				crca = int.from_bytes(self._readMsg.buf[getb],"little")
				crcb = self._hash(bytearray(list(self._readMsg)[0:getb]))
				if(crca != crcb):
					crcerr = True
			except Exception as error:
				print("err in main pull")
				print(error)
				print("sleeping it off")
				time.sleep(self._failSleepTime)
				return False
		if(crcerr):
			print("error detection caught 1")
			return False
		return True

	def sendConfirmation(self,flag):
		data= bytes('a', 'utf-8')
		if(flag):
			data = bytes('as', 'utf-8')#send sucess
		else:
			data = bytes('af', 'utf-8')#send fail
		write = i2c_msg.write(self._address,data)
		try:
			self._bus.i2c_rdwr(write)
		except Exception as error:
			print("err in ack")
			print(error)
			print("sleeping it off")
			time.sleep(self._failSleepTime)
			return False
		time.sleep(self._dt)
		return True
		
	def collect(self):
		ret =self.getPhoto()
		self.sendConfirmation(ret)
		if(ret):
			return True
		else:
			#try again
			ret =self.getPhoto()
			
			self.sendConfirmation(True)
			if(ret):
				return True
			else:
				print("Photo collection failed after retry")
		return False
         
	def getCurrentBuff(self):
		return self._buff[0:self._picLen]
		
	def saveCurrentBuff(self):
		time = datetime.datetime.now().strftime("%m:%d:%Y,%H:%M:%S")
		with open("storedPics/test"+time+"-"+"pic"+str(22)+".jpg", "wb") as f:
			f.write(bytearray(self._buff[0:self._picLen]))
			f.close()	
	
#cam1 = TCAM(0x55)
#cam1.begin()
#time.sleep(1)
#cam1.requestPhoto()
#print("get photo" + str(cam1.getPhoto()))
#print(cam1.getCurrentBuff())
#cam1.saveCurrentBuff()
#cam1.getCurrentBuff()
