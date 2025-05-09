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
    from _encHelper import PathValidator, trim_img
except ModuleNotFoundError:
    print(':: Encode Helper is MISSING...')
    qpause(message = ':: Press enter to continue...\n').ask()
    exit()

def configFile(inFile: Path):
    # Open the PNG image
    print(f':: Processing: {inFile}')
    img = Image.open(inFile).convert('RGBA')

    # Check if the image has 4 channels (RGBA)
    if img.mode != 'RGBA':
        print(':: ERROR: Only 4-channel (RGBA) PNG accepted!')
        return

    # Convert the image to a NumPy array for manipulation
    rgba = np.array(img)

    # Zero out pixels with alpha < 49
    alpha_mask = rgba[:, :, 3] < 49
    rgba[alpha_mask] = [0, 0, 0, 0]

    # Create the cleaned image
    cleaned_img = Image.fromarray(rgba, mode='RGBA')

    # Trim the transparent edges
    trimmed_img, (offset_x, offset_y) = trim_img(cleaned_img, threshold=19)
    
    # Log the original and trimmed sizes
    src_size = f'{img.width}x{img.height}'
    trim_size = f'{trimmed_img.width}x{trimmed_img.height}+{offset_x}+{offset_y}'
    print(f':: TRIM: {src_size} => {trim_size}')

    # Save the trimmed PNG
    trim_path = str(inFile).replace('.png', '_trim.png')
    trimmed_img.save(trim_path)
    print(f':: Trimmed PNG: {trim_path}')
    
    # Create a WebP version if the image is large
    if trimmed_img.width > 512 or trimmed_img.height > 512:
        webp_path = str(inFile).replace('.png', '_webp_512.webp')
        trimmed_img = trimmed_img.resize((512, 512), Image.Resampling.LANCZOS)
        trimmed_img.save(webp_path, 'WEBP', lossless=True)
        print(f':: Converted WebP: {webp_path}')

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
extList = ['.png']

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
