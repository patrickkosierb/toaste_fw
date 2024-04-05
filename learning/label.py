import cv2
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter

date = "04-04-24_20-40"

label = os.getcwd()+"/data_label/"
# run = len(os.listdir(label))+1
os.mkdir(label+date) #make new diretory for run
label = label+date

raw = "/mnt/c/Users/patri/Capstone/"+date+"/" #syncthing file path to run
raw_dir = os.listdir(raw)

if __name__ == '__main__':

    #sort the directory in decending order
    parse_raw = []
    for image in raw_dir:
        parse_raw.append(int(image[:len(image)-4]))
    parse_raw = sorted(parse_raw)

    raw_ordered = []
    for i in range(len(parse_raw)):
        raw_ordered.append((str(parse_raw[i])+".jpg"))

    # lls based on first and last pciture
    first_last = np.array([cv2.mean(cv2.imread(raw+raw_ordered[0]))[0:3],cv2.mean(cv2.imread(raw+raw_ordered[-1]))[0:3]])
    crispinesses = np.array([0,1])
    crispinesses = np.vstack([crispinesses, np.ones(2)]).T
    slope, intercept = np.linalg.lstsq(crispinesses, first_last, rcond=None)[0]
    M = slope[0]**2 + slope[1]**2 + slope[2]**2 

    # solve for crispiness given rgb and lls eqn found above 
    frames = []
    c_raw = []
    for picture in raw_ordered:
        frame = cv2.imread(raw+picture)
        frames.append(frame)
        y = cv2.mean(frame)[0:3] - intercept
        crisp = (slope[0]*y[0] + slope[1]*y[1] + slope[2]*y[2])/M
        c_raw.append(int(100*np.clip(crisp, 0, 1)))

    # apply filter for noise and label data 
    window_size = 31 
    poly_order = 3
    c_filtered = savgol_filter(np.array(c_raw), window_length=window_size, polyorder=poly_order)
    
    for i in range(len(raw_dir)):
        cv2.imwrite(label+"/crisp:"+str(int(c_filtered[i]))+".jpg",frames[i])
    print(len((os.listdir(label))))

    # plot lls vs filtered
    plt.plot(c_raw,marker='o', linestyle='', markersize=8)
    plt.plot(c_filtered,marker='o', linestyle='', markersize=8)
    plt.legend(["LLS Labeled Raw", "LLS Labeled Savgol"])
    plt.title("Labeling Crispiness")
    plt.xlabel("Picture number")
    plt.ylabel("Crispiness")
    plt.savefig("/mnt/c/Users/patri/Capstone/labeled/crisp-"+date+".png")




	