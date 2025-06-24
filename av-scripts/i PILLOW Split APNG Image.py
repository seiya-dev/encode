#!/usr/bin/env python3

import os
import re
import sys
import time
import subprocess

from pathlib import Path
from pathlib import PurePath

try:
    from questionary import text as qtext, press_any_key_to_continue as qpause
    from questionary import Choice, Validator, ValidationError
    from PIL import Image
    import numpy as np
except ModuleNotFoundError:
    print(':: Please install required modules: pip install numpy Pillow questionary')
    input(':: Press enter to continue...\n')
    exit()

try:
    from _encHelper import PathValidator, parse_apng, create_img, trim_img
except ModuleNotFoundError:
    print(':: Encode Helper or APNG Parser is MISSING...')
    qpause(message = ':: Press enter to continue...\n').ask()
    exit()

def configFile(inFile: Path):
    # Open the PNG image
    print(f':: Processing: {inFile}')
    outPath = inFile.replace('.png', '')
    
    data = open(inFile, 'rb').read()
    apng = parse_apng(data)
    apng.play_time_sec = apng.play_time / 1000
    apng.frame_cnt = len(apng.frames)
    
    print(f'ImageSize: {apng.width}x{apng.height}')
    print(f'PlayTime : {apng.play_time_sec}sec')
    print(f'NumPlays : {apng.num_plays}')
    print(f'Frames   : {apng.frame_cnt}')
    
    os.makedirs(outPath, exist_ok=True)
    
    merged = create_img(apng.width, apng.height)
    
    for i, frame in enumerate(apng.frames):
        # frame.data.save(f'{outPath}/frame_{i:04}.png')
        merged = Image.alpha_composite(merged, frame.data)
    
    # cleanup
    rgba = np.array(merged)
    alpha_mask = rgba[:, :, 3] < 49
    rgba[alpha_mask] = [0, 0, 0, 0]
    merged = Image.fromarray(rgba, mode='RGBA')
    # merged.save(f'{outPath}/merged.png')
    
    # trim frames
    trimmed_img, (offset_x, offset_y) = trim_img(merged, threshold=19)
    print(f'TrimData : {trimmed_img.width}x{trimmed_img.height}+{offset_x}+{offset_y}')
    cropData = (offset_x, offset_y, trimmed_img.width + offset_x, trimmed_img.height + offset_y)
    
    # prep avs script
    avsTemplate = ''
    
    # save cropped frames
    for i, frame in enumerate(apng.frames):
        frame.data = frame.data.crop(cropData)
        frame.data.save(f'{outPath}/frame_{i+1:04}.png')
        avsFunc = f'LoadFrameImage("./{Path(outPath).name}/frame_{i+1:04}.png", {frame.delay_den}, {frame.delay_num})\n'
        if i == 0:
            avsTemplate += f'v =     {avsFunc}'
        else:
            avsTemplate += f'v = v + {avsFunc}'
    
    # save avs script
    avsTemplate += 'last = v\n'
    avsTemplate += 'ConvertToPlanarRGBA()\n'
    avsTemplate += 'videoAddPadMod2()\n'
    avsTemplate += 'ConvertToYUV420()\n'
    open(f'{outPath}.avs', 'w', encoding='utf-8').write(avsTemplate)

# folder
def configFolder(inPath: Path):
    inFile = list()
    
    for file in os.listdir(inPath):
        file = os.path.join(inPath, file)
        fileExt = PurePath(file).suffix.lower()
        if extList.count(fileExt) > 0:
            inFile.append(file)
    
    for i in range(len(inFile)):
        configFile(inFile[i])

# set folder
if len(sys.argv) < 2:
    inputPath = qtext(':: Folder/File: ', validate=PathValidator).ask()
    inputPath = inputPath.strip('\"')
else:
    inputPath = sys.argv[1]

# to abs path
inputPath = os.path.abspath(inputPath)
extList = ['.apng', '.png']

# check path
try:
    if os.path.isfile(inputPath):
        fileExt = PurePath(inputPath).suffix.lower()
        if extList.count(fileExt) > 0:
            print(f':: Input File: {inputPath}')
            configFile(inputPath)
        else:
            print(f':: Input file is not a png file: {inputPath}')
    elif os.path.isdir(inputPath):
        print(f':: Input Folder: {inputPath}')
        configFolder(inputPath)
    else:
        print(f':: Input path is not a folder or png file: {inputPath}')
except Exception as err:
    print(f':: Something goes wrong...')
    print(f':: {type(err).__name__}: {err}')

# end
if os.environ.get('isBatch') is None:
    qpause(message = '\n:: Press enter to continue...\n').ask()
