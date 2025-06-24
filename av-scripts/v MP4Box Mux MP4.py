#!/usr/bin/env python3

import os
import re
import sys
import time
import tempfile
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
from _encHelper import getMediaData, audioTitle, searchMedia, searchSubsFile

inputTypesVideo = ['.264', '.h264', '.avc', '.m4v', '.mp4', '.avi']
inputTypesAudio = ['.aac', '.m4a', '.mp3', '.mp4', '.avi']

inputTypes = list()
inputTypes.extend(inputTypesVideo)
inputTypes.extend(inputTypesAudio)

# file
def configFile(inFile: Path):
    outFolder = str(PurePath(inFile).parent)
    prefix    = str(PurePath(inFile).stem)
    fileExt   = PurePath(inFile).suffix.lower()
    outFile   = f'{outFolder}/{PurePath(inFile).stem} [mux]'
    tempPath  = tempfile.gettempdir()
    
    audioFile = ''
    audioList = list()
    if ['.mp4', '.avi'].count(fileExt) > 0:
        audioList.append(Choice(f'[audio]: {prefix}{fileExt}', value=inFile))
    
    extAudioList = searchMedia(outFolder, prefix, inputTypesAudio)
    for audioFile in extAudioList:
        audioList.append(Choice(f'[audio]: {audioFile.name}', value=audioFile.path))
    audioList.append(Choice(f'[audio]: no audio', value=''))
    
    videoTitle = ''
    if inputTypesVideo.count(fileExt) > 0:
        videoTitle = questionary.text('Set Video Title:').ask()
        videoTitle = f':name={videoTitle}'
    
    videoFPS = ''
    if inputTypesVideo.count(fileExt) > 0:
        videoFPSList = [ 'Unchanged', '23.976', '24.000', '25.000', '29.970', '30.000', '48.000', '50.000', '59.940', '60.000' ]
        videoFPS = questionary.select('Video FPS value:', choices = videoFPSList).ask()
        videoFPS = '' if videoFPS == 'Unchanged' else f':fps={videoFPS}'
    
    audioLang = ''
    if len(audioList) > 0:
        audioFile = questionary.select('Select Audio File:', audioList).ask()
        if audioFile != '':
            audioLang = questionary.text('Set Audio Language (ISO 639-2):').ask()
    
    mp4box = list()
    mp4box.extend(['mp4box', '-for-test'])
    mp4box.extend(['-tmp', tempPath])
    mp4box.extend(['-brand', 'mp42'])
    # mp4box.extend(['-ab', 'iso2', '-ab', 'mp41', '-ab', 'isom'])
    # mp4box.extend(['--mpeg4-comp-brand', 'mp42,iso6,isom,msdh,dby1'])
    # mp4box.extend(['--dv-profile', '8'])
    # mp4box.extend(['--dv-bl-compatible-id', '6'])
    
    if inputTypesVideo.count(fileExt) > 0:
        mp4box.extend(['-add', f'{inFile}#video{videoFPS}{videoTitle}' ])
        outFile   = f'{outFile}.mp4'
    else:
        outFile   = f'{outFile}.m4a'
    
    if audioFile != '':
        mp4box.extend(['-add', f'{audioFile}#audio:name=:lang={audioLang}'])
    
    mp4box.extend(['-new', f'{outFile}'])
    
    startTime = time.monotonic()
    subprocess.run(mp4box)
    
    runTime = time.monotonic() - startTime
    hours, rem = divmod(runTime, 3600)
    minutes, seconds = divmod(rem, 60)
    print(f'\n:: Remuxed {PurePath(outFile).name} in {hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}')

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
        if inputTypes.count(fileExt) > 0:
            print(f':: Input File: {inputPath}')
            configFile(inputPath)
        else:
            print(f':: Input file is not allowed: {inputPath}')
    elif os.path.isdir(inputPath):
        print(f':: Input Folder: {inputPath}')
        configFolder(inputPath)
    else:
        print(f':: Input path is not a folder or video/audio file: {inputPath}')
except Exception as err:
    print(f':: Something goes wrong...')
    print(f':: {type(err).__name__}: {err}')

# end
if os.environ.get('isBatch') is None:
    questionary.press_any_key_to_continue(message = '\n:: Press enter to continue...\n').ask()
