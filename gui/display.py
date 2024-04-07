import numpy as np
import os
from PIL import Image

buf = np.memmap('/dev/fb0', dtype='uint16',mode='w+', shape=(320,240))
buf[:] = 0xffff

image_buffer = np.full((320,240),0xffc0,dtype='uint16')


def write_to_display(image):
    global buf, image_buffer
    image = image.convert('RGB')
    pix = image.load()  #load pixel array
    for h in range(0,image.size[1]):
        for w in range(0,image.size[0]):#320
            R=pix[w,h][0]>>3
            G=pix[w,h][1]>>2
            B=pix[w,h][2]>>3
            rgb=(R<<11) | (G<<5) | B
            image_buffer[319-w][h] = rgb
    buf[:] = image_buffer[:]
    

