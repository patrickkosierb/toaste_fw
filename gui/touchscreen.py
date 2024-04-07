import evdev
import threading

touchscreen_thread = None
pressed = 0
xpos = 0
ypos = 0
SYMIN = 350
SYMAX = 3750
AYMAX = 240
SXMIN = 250
SXMAX = 3850
AXMAX = 320
press = None
release = None
drag = None
device_path = ""
    

def Start_Touchscreen(pressF,releaseF,dragF):
	global press,release,drag ,touchscreen_thread,device_path
	press = pressF
	release = releaseF
	drag = dragF
	devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
	for device in devices:
		if device.name == "stmpe-ts":
			device_path=device.path
	if device_path =="":
		print("touch screen not found")
	else:
		touchscreen_thread = threading.Thread(target=TouchscreenFunc, args=())
		touchscreen_thread.start()
	
def TouchscreenFunc():
	dev = evdev.InputDevice(device_path)
	dev.grab()
	for event in dev.read_loop():
		global pressed,xpos,ypos,SYMIN,SYMAX,AYMAX,SXMIN,SXMAX,AXMAX,press,release,drag
		if(event.type==3):
			if(event.code==0):
				ypos = round((event.value-SYMIN)/(SYMAX-SYMIN)*AYMAX)
			if(event.code==1):
				xpos = AXMAX - round((event.value-SXMIN)/(SXMAX-SXMIN)*AXMAX)
				drag(pressed,xpos,ypos)#execute drag
		elif (event.type ==1):
			pressed = event.value
			if(event.value==1):
				press(xpos,ypos)#execute press
			else:
				release(xpos,ypos)#execute release
				
def tpress(x,y):
	print("Btn down at X:"+str(xpos)+" Y: "+str(ypos))
	pass
def trelease(x,y):
	print("Btn up at X:"+str(xpos)+" Y: "+str(ypos))
	pass
def tdrag(press,x,y):
	pass

