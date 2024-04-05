
import cv2
import numpy as np
import os 
from PIL import Image
from crisp_net import CrispClassifier
from io import BytesIO

model = CrispClassifier()
model.load()
    
with open(os.getcwd()+"/learning/data_label/04-04-24_20-40/crisp:7.jpg", "rb") as f: #random pics
    jpeg_data = f.read()

byte_array = bytes(jpeg_data)
img = Image.open(BytesIO(byte_array))
c1_cur_crispiness = model.predictCrispiness(img)
print(c1_cur_crispiness)

# img = Image.open(os.getcwd()+"/learning/data_label/04-04-24_20-40/crisp:26.jpg")
# c1_cur_crispiness = model.predictCrispiness(img)
# print(c1_cur_crispiness)
