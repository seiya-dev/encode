#!/usr/bin/env python3

import os
import re
import sys
import time
import subprocess

from pathlib import Path
from pathlib import PurePath

try:
    import questionary
    from questionary import Choice, Validator, ValidationError
except ModuleNotFoundError:
    print(':: Please install "questionary" module: pip install questionary')
    input(':: Press enter to continue...\n')
    exit()

from _encHelper import boolYN, IntValidator, PathValidator, extVideoFile, fixPath
from _encHelper import getMediaData, audioTitle, searchSubsFile

def cutFile(inPath: Path):
    vFPS = questionary.select(
        'Video FPS value:', 
        choices = [ '24000/1001','25/1','30000/1001','30/1','60/1' ],
    ).ask()
    
    sFrame = questionary.text('Start Frame:', validate=IntValidator).ask()
    eFrame = questionary.text('End Frame:  ', validate=IntValidator).ask()
    
    sFrame = int(sFrame)
    eFrame = int(eFrame)
    vFPS   = list(map(int, vFPS.split('/')))
    
    if not sFrame < eFrame:
        print(f':: Wrong input:\n  Start: {sFrame}\n  End  : {eFrame}')
        return
    
    sTime = sFrame / vFPS[0] * vFPS[1]
    eTime = eFrame / vFPS[0] * vFPS[1]
    
    sTime = round(sTime, 11)
    eTime = round(eTime, 11)
    
    print(f':: TIME RANGE: {sTime}-{eTime} ({sFrame}-{eFrame})');
    
    inDir   = PurePath(inPath).parent
    inFile  = os.path.abspath(inPath)
    inFName = os.path.join(inDir, PurePath(inFile).stem)
    # -type [aac/ac3/mp3/mp2/mpa/wav/dts/dtswav/ddwav]
    
    splCmd = [
        r'besplit',
        '-core(', '-input', f'{inFile}', '-prefix', f'{inFName}-new', '-type', 'aac', '-a', ')',
        '-split(', f'{sTime}', f'{eTime}', ')',
    ]
    
    # print(' '.join(splCmd))
    subprocess.run(splCmd)

# folder
def configFolder(inPath: Path):
    print(f'\n:: Selected path: {os.path.abspath(inPath)}')
    print(f'script not usable for dir!')

# set folder
if len(sys.argv) < 2:
    inputPath = questionary.text(':: Folder/File: ', validate=PathValidator).ask()
    inputPath = inputPath.strip('\"')
else:
    inputPath = sys.argv[1]

# to abs path
inputPath = os.path.abspath(inputPath)

# check path
try:
    if os.path.isfile(inputPath):
        fileExt = PurePath(inputPath).suffix.lower()
        if ['.aac'].count(fileExt) > 0:
            print(f':: Input file: {inputPath}')
            configFile(inputPath)
        else:
            print(f':: Input file is not a video file: {inputPath}')
    elif os.path.isdir(inputPath):
        print(f':: Input folder: {inputPath}')
        configFolder(inputPath)
    else:
        print(f':: Input path is not a folder or video file: {inputPath}')
except Exception as err:
    print(f':: Something goes wrong...')
    print(f':: {type(err).__name__}: {err}')

# end
if os.environ.get('isBatch') is None:
    questionary.press_any_key_to_continue(message = '\n:: Press enter to continue...\n').ask()
