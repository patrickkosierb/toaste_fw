import cv2
import os
import numpy as np

raw = os.getcwd()+"/data_raw/" 
label = os.getcwd()+"/data_label/"

if __name__ == '__main__':

    number_of_images = len(os.listdir(raw))
    average_colours = []
    first_last = []
    crispinesses = np.array(np.linspace(0, 1, 2))
    c = []

    # get first and last data points
    maxCrispframe = os.listdir(raw)[-1]
    minCrispframe = os.listdir(raw)[0]

    # get rbg values
    first_last.append(cv2.mean(cv2.imread(raw+minCrispframe))[0:3])
    first_last.append(cv2.mean(cv2.imread(raw+maxCrispframe))[0:3])

    # lls
    crispinesses = np.vstack([crispinesses, np.ones(2)]).T
    slope, intercept = np.linalg.lstsq(crispinesses, first_last, rcond=None)[0]

    # label training data with crispiness from lls
    M = slope[0]**2 + slope[1]**2 + slope[2]**2 
    for picture in os.listdir(raw):
        frame = cv2.imread(raw+picture)
        average_colours = (cv2.mean(frame)[0:3])
        y = average_colours - intercept

        crisp = np.clip((slope[0]*y[0] + slope[1]*y[1] + slope[2]*y[2])/M, 0, 1)
        c.append(int(crisp*100))

        cv2.imwrite(label+"/crisp-"+str(c[-1])+".jpg",frame)





	