import time
import datetime
from PIL import Image
import display
import touchscreen
import math
toastGIF = []

screen = 0
requires_update = 0

for i in range(0,11):
    numstr = "0"+str(i)
    if i >9:
        numstr=str(i)
    toastGIF.append(Image.open("frame_"+numstr+".png").convert('RGBA'))

image = Image.new('RGBA', (320, 240))



def press_callback(x,y):
	global screen, requires_update
	print("hello")
	screen = 1
	requires_update = 1
	pass

def release_callback(x,y):
	pass
	
def drag_callback(pressed,x,y):
	pass

touchscreen.Start_Touchscreen(press_callback,release_callback,drag_callback)
start_time = datetime.datetime.now()

last_delta = -1
while True:
	if(screen == 0):
		current_time = datetime.datetime.now()
		delta_t = math.floor(int((current_time-start_time).total_seconds()*1000)/100)
		if delta_t>10:
			delta_t=0
			start_time = datetime.datetime.now()
		if delta_t != last_delta:
			image.paste((255,255,255),(0, 0, image.size[0], image.size[1]))
			image.paste(toastGIF[delta_t],(80,40),toastGIF[delta_t])
			display.write_to_display(image)
	if(screen == 1):
		if requires_update:
			image.paste((255,55,255),(0, 0, image.size[0], image.size[1]))
			display.write_to_display(image)
			requires_update =0 
	time.sleep(0.01)

	
