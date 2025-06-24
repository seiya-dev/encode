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

# file
def configFile(inFile: Path):
    print(f'\n:: Checking: {PurePath(inFile).name}')
    
    encCmd = list()
    encCmd.extend([ r'ffmpeg', '-hide_banner', ])
    encCmd.extend([ '-loglevel', 'error', '-stats', ])
    encCmd.extend([ '-hwaccel', 'auto', ])
    encCmd.extend([ '-i', inFile ]);
    encCmd.extend([ '-f', 'null', '-' ]);
    
    startTime = time.monotonic()
    subprocess.run(encCmd)
    
    runTime = time.monotonic() - startTime
    hours, rem = divmod(runTime, 3600)
    minutes, seconds = divmod(rem, 60)
    print(f'\n:: Checked {PurePath(inFile).name} in {hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}')

# folder
def configFolder(inPath: Path):
    inFile = list()
    
    for file in os.listdir(inPath):
        file = os.path.join(inPath, file)
        fileExt = PurePath(file).suffix.lower()
        if extVideoFile.count(fileExt) > 0 or extAudioFile.count(fileExt) > 0:
            inFile.append(file)
    
    for i in range(len(inFile)):
        configFile(inFile[i])

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
        if extVideoFile.count(fileExt) > 0 or extAudioFile.count(fileExt) > 0:
            print(f':: Input File: {inputPath}')
            configFile(inputPath)
        else:
            print(f':: Input file is not a video/audio file: {inputPath}')
    elif os.path.isdir(inputPath):
        print(f':: Input Folder: {inputPath}')
        configFolder(inputPath)
    else:
        print(f':: Input path is not a folder or video file: {inputPath}')
except Exception as err:
    print(f':: Something goes wrong...')
    print(f':: {type(err).__name__}: {err}')

# end
if os.environ.get('isBatch') is None:
    questionary.press_any_key_to_continue(message = '\n:: Press enter to continue...\n').ask()
