import cv2
import os
import numpy as np

path = os.getcwd() + '\\images\\'

number_of_images = len(os.listdir(path))
average_colours = []
crispinesses = np.array(np.linspace(0, 1, number_of_images))

if __name__ == '__main__':
    for i in range(number_of_images):
        average_colours.append(cv2.mean(cv2.imread(path + 'toast' + str(i) + '.png'))[0:3])

    crispinesses = np.vstack([crispinesses, np.ones(len(crispinesses))]).T

    slope, intercept = np.linalg.lstsq(crispinesses, average_colours, rcond=None)[0]

    slope = list(slope)
    intercept = list(intercept)

    f = open('parameters.py', 'w')
    f.write('slope = ' + str(slope) + '\n')
    f.write('intercept = ' + str(intercept))
    f.close()