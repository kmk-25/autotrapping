from vimba import *
import numpy as np
import matplotlib.pyplot as plt
import sys
import time
import os
import glob
import re
from time import sleep
from skimage.registration import phase_cross_correlation as pcc
from skimage.io import imread as imread
import subprocess


def processError(e, attemptNumber, DEBUG=False):
    '''
    error handling function: to reset USB if Error -13
    to be tested
    '''
    batchscript = r"C:/Users/gravity_2/Documents/gautam/heightFeedback_ZMQ/resetMako_cmd.bat"
    if DEBUG:
        print('type: ', type(e), '\nmsg: ', e.args[0],\
               '\ndatetime: ', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    if '<AccessMode.None_: 0>' in e.args[0]:
        if DEBUG:
            print('\n-> because GUI is open')
    elif '<VmbError.Other: -13>' in e.args[0] or '<VmbError.Timeout: -12>' in e.args[0]:
        print(f'\nresetting USB ... Try #{attemptNumber+1} ')
        # out = os.system(batchscript)
        subprocess.run(batchscript, shell=True, check=True)
        sleep(3)
    else:
        # For good measure...
        print(f'\nresetting USB ... Try #{attemptNumber+1} ')
        # out = os.system(batchscript)
        subprocess.run(batchscript, shell=True, check=True)
        sleep(3)


def take_image_std():
    max_retries = 5
    attempts = 0
    while attempts<max_retries:
        with Vimba.get_instance() as vimba:
            try:
                with vimba.get_camera_by_id('DEV_1AB2280007F6') as camera:
                    print(f'Connected to {camera.get_model()}')
                    camera.ExposureTime.set(900)
                    camera.Gain.set(20) # Should be tuned after adding ND
                    camera.Gamma.set(1.0)
                    camera.set_pixel_format(PixelFormat.Mono8)
                    frame = camera.get_frame()
                    #frame.convert_pixel_format(PixelFormat.Mono16)
                    img = frame.as_numpy_ndarray()
                    std_val = np.std(img)
                    return std_val
            except VimbaCameraError as e:
                print(f'Did you quit the vimba viewer for the camera being accessed???')
                print(e)
                # Also, try resetting the USB interface as this seems to be a known failure mode...
                processError(e, attempts)
                attempts += 1

def take_image_height(filename, saveFile=True):
    max_retries = 5
    attempts = 0
    while attempts<max_retries:
        with Vimba.get_instance() as vimba:
            try:
                with vimba.get_camera_by_id('DEV_1AB2280007F6') as camera:
                    print(f'Connected to {camera.get_model()}')
                    camera.ExposureTime.set(45)
                    camera.Gain.set(0) # Should be tuned after adding ND
                    camera.Gamma.set(1.0)
                    camera.set_pixel_format(PixelFormat.Mono8)
                    frame = camera.get_frame()
                    #frame.convert_pixel_format(PixelFormat.Mono16)
                    img = frame.as_numpy_ndarray()
                    #img = img[2100:2900, 2500:3000]
                    if saveFile:
                        np.save(f'{filename}',img)
                        print(f'Saved to {filename}')  
                    return
            except VimbaCameraError as e:
                print(f'Did you quit the vimba viewer for the camera being accessed???')
                print(e)
                # Also, try resetting the USB interface as this seems to be a known failure mode...
                processError(e, attempts)
                attempts += 1

def get_height_from_image(path):

    heightList = []
    lateralList = []
    time_info = []

    shift=[0,0]
    folder="run" 
    dest = os.path.join(path,folder)
    if not os.path.exists(dest):
        os.makedirs(dest)
    height_info_path = os.path.join(dest, "height_info.npy")
    if os.path.exists(height_info_path):
        heightList = np.load(height_info_path).tolist()
        lateralList = np.load(os.path.join(dest, "lateral_info.npy"),lateralList)
        time_info = np.load(os.path.join(dest, "time_info.npy"),lateralList)
    
    run=0
    existing_files = glob.glob(os.path.join(dest, "image_test_*.npy"))
    if existing_files:
        numbers = [
            int(re.search(r'image_test_(\d+)\.npy', os.path.basename(f)).group(1))
            for f in existing_files if re.search(r'image_test_(\d+)\.npy', os.path.basename(f))
        ]
        if numbers:
            run = max(numbers) + 1

    time_info.append(time.time())
    suffix = f'image_test_{run}.npy'
    filename=os.path.join(dest,suffix)
    take_image_height(filename)
    if run>0:    
        zeroth_image=np.load((os.path.join(dest,"image_test_0.npy")))
        image=np.load(filename)
        shift,_,_ = pcc(threshold_image(zeroth_image,50,),threshold_image(image,50,),upsample_factor=100) #hard coded for now
    else:
        shift=[0,0]
    heightList.append(shift[0])
    lateralList.append(shift[1])
    np.save(os.path.join(dest,"height_info.npy"),heightList)
    np.save(os.path.join(dest,"lateral_info.npy"),lateralList)
    np.save(os.path.join(dest,"time_info.npy"),time_info)
    return shift[0]#+height    return height

def threshold_image(img,lower=0,upper=480):
    img2 = img.copy()
    mask = (lower < img2) & (img2 < upper)
    img2[mask] = upper
    img2[~mask] = lower
    return img2
