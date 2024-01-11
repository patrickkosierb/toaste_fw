import cv2
import sys
import numpy as np
from parameters import slope, intercept

# Eventually these will just be hard coded
slope = np.array(slope)
intercept = np.array(intercept)

vid = cv2.VideoCapture(0)

crispiness = float(sys.argv[1])

def crispiness_to_colour(crispiness):
    return np.multiply(crispiness, slope) + intercept

def expand_colour_range(colour, tolerance = 10):
    ranges = []
    for i in range(3):
        ranges.append([colour[i] - tolerance, colour[i] + tolerance])
    return ranges

def toast_done():
    print("Done!")


ranges = expand_colour_range(crispiness_to_colour(crispiness))
blue_range, green_range, red_range = ranges[0], ranges[1], ranges[2]

print("Target:\t\t", crispiness_to_colour(crispiness))
  
while(True): 
    # Capture the video frame by frame 
    ret, frame = vid.read()

    # Mirror the frame (it just looks better but we can remove this later)
    frame = cv2.flip(frame, 1)

    # Display the frame and get average colour
    cv2.imshow('frame', frame)
    average = np.array(cv2.mean(frame)[0:3])

    print("Current:\t", average, end='\r')

    # Done if average colour is within a certain range
    if blue_range[0] < average[0] < blue_range[1] and green_range[0] < average[1] < green_range[1] and red_range[0] < average[2] < red_range[1]:
        toast_done()
        break
      
    # Quit with 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'): 
        break

vid.release() 
cv2.destroyAllWindows()