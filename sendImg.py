# importing the requests library
import requests  #pip install requests 
import random
import datetime
 
# api-endpoint
URL = "http://192.168.40.50:3000/"

def sendBuffers(imgBuff,deltaTBuff):
    try:
        senDate = datetime.datetime.now().strftime('%m-%d-%y_%H-%M')
        data = {"sender":"Toast-e","imgArr":imgBuff,"date":senDate,"times":deltaTBuff}
        r = requests.post(url = URL, data = data)
        # extracting data in json format
        print('imgs sent')
    except:
        print('img transmittion failure')

