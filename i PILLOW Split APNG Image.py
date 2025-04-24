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
    import _apngParser as APNG
    from _encHelper import PathValidator
except ModuleNotFoundError:
    print(':: Encode Helper or APNG Parser is MISSING...')
    qpause(message = ':: Press enter to continue...\n').ask()
    exit()

def create_png(width, height):
    return Image.new('RGBA', (width, height), (0, 0, 0, 0))

def trim_image(img, threshold=19):
    # Get the alpha channel (transparency)
    alpha = img.getchannel('A')
    alpha_np = np.array(alpha)
    
    # Create a mask where alpha is above the threshold
    mask = alpha_np > int(threshold / 100 * 255)
    if not np.any(mask):
        return img, (0, 0)

    # Get the bounding box of the non-transparent region
    coords = np.argwhere(mask)
    y0, x0 = coords.min(axis=0)
    y1, x1 = coords.max(axis=0) + 1  # slices are exclusive
    trimmed_img = img.crop((x0, y0, x1, y1))
    return trimmed_img, (x0, y0)

def configFile(inFile: Path):
    # Open the PNG image
    print(f':: Processing: {inFile}')
    outDir = inFile.replace('.png', '')
    
    data = open(inFile, 'rb').read()
    apng = APNG.apng_disassemble(data)
    apng.play_time_sec = apng.play_time / 1000
    apng.frame_cnt = len(apng.frames)
    
    print(f'ImageSize: {apng.width}x{apng.height}')
    print(f'PlayTime : {apng.play_time_sec}sec')
    print(f'NumPlays : {apng.num_plays}')
    print(f'Frames   : {apng.frame_cnt}')
    
    os.makedirs(outDir, exist_ok=True)
    
    merged = create_png(apng.width, apng.height)
    
    for i, frame in enumerate(apng.frames):
        # frame.data.save(f'{outDir}/frame_{i:04}.png')
        merged = Image.alpha_composite(merged, frame.data)
    
    # cleanup
    rgba = np.array(merged)
    alpha_mask = rgba[:, :, 3] < 49
    rgba[alpha_mask] = [0, 0, 0, 0]
    merged = Image.fromarray(rgba, mode='RGBA')
    # merged.save(f'{outDir}/merged.png')
    
    # trim frames
    trim_img, (offset_x, offset_y) = trim_image(merged, threshold=19)
    print(f'TrimData : {trim_img.width}x{trim_img.height}+{offset_x}+{offset_y}')
    cropData = (offset_x, offset_y, trim_img.width + offset_x, trim_img.height + offset_y)
    
    # prep avs script
    avsTemplate = ''
    
    # save cropped frames
    for i, frame in enumerate(apng.frames):
        frame.data = frame.data.crop(cropData)
        frame.data.save(f'{outDir}/frame_{i+1:04}.png')
        print(frame.delay_ms)
    
    """
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
    trimmed_img, (offset_x, offset_y) = trim_transparent_edges(cleaned_img, threshold=19)
    
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
    """

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
