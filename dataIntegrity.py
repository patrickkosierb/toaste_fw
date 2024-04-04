from i2ctest import TCAM
import sendImg
import time

buff = []
tbuff = []
sleepTime = 0.1

cam1 = TCAM(0x55)
cam1.begin()

for i in range (0,100):
    time.sleep(sleepTime)
    cam1.requestPhoto()
    cam1.getPhoto()
    buff.append(cam1.getCurrentBuff())
    tbuff.append(i*sleepTime*1000)

sendImg.sendBuffers(buff,tbuff)
    
    
