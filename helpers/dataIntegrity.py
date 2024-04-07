from i2ctest import TCAM
import sendImg
import time

buff = []
tbuff = []
sleepTime = 0.001

cam1 = TCAM(0x55)
cam1.begin()
print("begin")
for i in range (0,20):
    print(i)
    time.sleep(sleepTime)
    ret = cam1.requestPhoto()
    if(ret):
        print("photo requested")
        ret =cam1.collect()
        if(ret):
            buff.append(cam1.getCurrentBuff())
            tbuff.append(round(i*sleepTime*1000))
sendImg.sendBuffers(buff,tbuff)
print("done")
    
    
