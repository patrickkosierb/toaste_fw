import time
import datetime
from PIL import Image, ImageDraw, ImageFont
import display
import math
import threading

toastGIF = []
slider_img = Image.open("images/slider.png").convert('RGBA')
start_img = Image.open("images/start.png").convert('RGBA')
button_callback = None
start_time = datetime.datetime.now()
for i in range(0,11):
    numstr = "0"+str(i)
    if i >9:
        numstr=str(i)
    toastGIF.append(Image.open("images/frame_"+numstr+".png").convert('RGBA'))

image = Image.new('RGBA', (320, 240))
ctx = ImageDraw.Draw(image)
white = (255,255,255)
red = (171,19,19)
black=(0,0,0)
base_toast = [255,216,158]
base_crust = [178,127,68]
fnt_toaste = ImageFont.truetype('images/OpenSans.ttf', 36)
fnt_subhead = ImageFont.truetype('images/OpenSans.ttf', 20)
fnt_head = ImageFont.truetype('images/OpenSans.ttf', 28)
fnt_small = ImageFont.truetype('images/OpenSans.ttf', 16)

slider_pos = 40
screen = 0
requires_update = 1
last_delta = -1
gui_thread = None

#def press_callback(x,y):
#	global screen, requires_update, button_callback, slider_pos
#	if(screen == 1):
#		if(x>230):
#			screen = 2
#			button_callback(slider_pos)
#	requires_update = 1
#
#def release_callback(x,y):
#	pass
#	
#def drag_callback(pressed,x,y):
#	global screen, requires_update, slider_pos
#	if(screen==1):
#		if(x<220):
#			if(y<70):
#				slider_pos = 100
#			elif(y>=70 and y<=210):
#				slider_pos	= int((210 -y)/(210-70)*100)
#			else:
#				slider_pos = 0
#			requires_update = 1
#


def color_adj(base):
	global slider_pos
	return int(base-(base)*slider_pos/100)

def draw_toast():
	global ctx
	bread = (color_adj(base_toast[0]),color_adj(base_toast[1]),color_adj(base_toast[2]))
	crust = (color_adj(base_crust[0]),color_adj(base_crust[1]),color_adj(base_crust[2]))
	offset= 20
	startx = 5
	starty = 60
	width = 130
	height = 120
	ctx.rectangle((startx,starty+offset+20,startx+width,starty+offset+40),fill=crust)
	ctx.ellipse((startx,starty+offset+20,startx+width,starty+offset+60),fill=crust)
	ctx.rectangle((startx+15,starty+height,startx+width-15, starty+height+offset+20),fill=crust)
	ctx.rectangle((startx,starty+20,startx+width,starty+40),fill=bread)
	ctx.ellipse((startx,starty+20,startx+width,starty+60),fill=bread)
	ctx.rectangle((startx+15,starty+40,startx+width-15,starty+height+20),fill=bread)
	ctx.ellipse((startx,starty,startx+width,starty+40),fill=bread)
	
def draw_silder():
	global ctx
	#73 to 217
	strtxt = str(slider_pos)
	if(slider_pos<10):
		strtxt = "00"+str(slider_pos)
	elif(slider_pos<100):
		strtxt = "0"+str(slider_pos)
	ctx.line((155, 210-+slider_pos*(210-70)/100, 205, 210-slider_pos*(210-70)/100), fill=(255, 255,255,80), width=2)
	ctx.text((160,140),strtxt+"%",font=fnt_small,fill=white)
	
def guiFunc():
	global start_time,image,ctx,requires_update
	while True:
		if(screen == 0):
			current_time = datetime.datetime.now()
			delta_t = math.floor(int((current_time-start_time).total_seconds()*1000)/100)
			if delta_t>10:
				delta_t=0
				start_time = datetime.datetime.now()
			if delta_t != last_delta:
				image.paste(red,(0, 0, image.size[0], 40))
				image.paste(white,(0, 40, image.size[0], image.size[1]))
				image.paste(toastGIF[delta_t],(80,40),toastGIF[delta_t])
				ctx.text((90,-5),"Toast-E",font=fnt_toaste,fill=white)
				ctx.text((10,200),"Insert toastable to begin toasting",font=fnt_subhead,fill=black)
				
				display.write_to_display(image)
		elif(screen == 1):
			if requires_update:
				image.paste(white,(0, 0, image.size[0], image.size[1]))
				draw_toast()
				image.paste(red,(0, 0, image.size[0], 40))
				ctx.text((15,-5),"Select your preference",font=fnt_head,fill=white)
				image.paste(slider_img,(150,60),slider_img)
				draw_silder()
				ctx.ellipse((235,105,305,105+70),fill=red)
				image.paste(start_img,(240,110),start_img)
				display.write_to_display(image)
				requires_update =0 
		elif(screen == 2):
			if requires_update:
				image.paste(red,(0, 0, image.size[0], 40))
				image.paste(white,(0, 40, image.size[0], image.size[1]))
				ctx.text((90,-5),"Toast-E",font=fnt_toaste,fill=white)
				ctx.text((70,200),"We're cooking!",font=fnt_subhead,fill=black)
				display.write_to_display(image)
				requires_update =0 
		time.sleep(0.01)

def init(cb):
	global start_time,button_callback, touchscreen, gui_thread
	button_callback=cb
	start_time = datetime.datetime.now()
	gui_thread = threading.Thread(target=guiFunc, args=())
	gui_thread.start()
	
def setState(state):
	global screen,requires_update
	screen = state
	requires_update = 1

def press(short):
    global screen, requires_update,slider_pos
    if(screen == 1):
    	if(short):
    		slider_pos=slider_pos+10
			if(slider_pos>100):
				slider_pos = 10
        else:
			screen =2
			button_callback(slider_pos)
		requires_update = 1
def tfunc(asss):
	pass
	
init(tfunc)
