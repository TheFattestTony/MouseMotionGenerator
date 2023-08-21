import cv2
import pyautogui
from PIL import Image
import numpy as np
import pandas as pd


def fastroi(nomeimg, nomesave):
    im = cv2.imread(nomeimg)
    roi = cv2.selectROI(im)
    print(roi)
    roi_cropped = im[int(roi[1]):int(roi[1] + roi[3]), int(roi[0]):int(roi[0] + roi[2])]
    cv2.imshow('ROI', roi_cropped)
    cv2.imwrite(nomesave, roi_cropped)
    cv2.waitKey(0)


def fastslice(nomeimage, namesave, x, y, w, h) :
    im = Image.open(nomeimage)
    (left, top, right, bottom) = (x, y, x + w, y + h)
    im1 = im.crop((left, top, right, bottom))
    im1.save(namesave)


def color(im):
    img1 = cv2.imread(im)
    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    cv2.imwrite('cursor_gray2.png', img1_gray)


#fastslice('cursor_720.png', 'cursor_2.png', 4, 2, 25, 30)
while True:
    print(pyautogui.position())

