# importing the requests library
import requests  #pip install requests 
import random
import datetime
 
# api-endpoint
URL = "http://192.168.40.50:3000/"

def sendBuffers(imgBuff,deltaTBuff):
    try:
        senDate = datetime.datetime.now().strftime('%m-%d-%y_%H-%M')
        tBuff=[]
        for img in imgBuff:
            imgStr=""
            for num in img:
                hexs = format(ord(chr(num)),"x")
                if len(hexs)==1:
                    hexs="0"+hexs
                imgStr+=hexs
            tBuff.append(imgStr)
        print(len(tBuff))
        data = {"sender":"Toast-e","imgArr":tBuff,"date":senDate,"times":deltaTBuff}
        r = requests.post(url = URL, data = data)
        # extracting data in json format
        print('imgs sent')
    except Exception as error:
        print('img transmittion failure:', error)

