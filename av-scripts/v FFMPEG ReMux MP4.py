#!/usr/bin/env python3

# set libs
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
extAudioFile = ['.aac']

# file
def configFile(inFile: Path):
    outFolder = PurePath(inFile).parent
    outFile   = f'{outFolder}/{PurePath(inFile).stem} [remux]'
    inFonts = fixPath(f'{outFolder}/fonts', True)
    
    noVideo = False
    
    videoData = getMediaData(inFile, 'v', True)
    if len(videoData) < 1:
        noVideo = True
        outFile = f'{outFile}.m4a'
    else:
        outFile = f'{outFile}.mp4'
    
    audioList = list()
    audioData = getMediaData(inFile, 'a')
    for t in range(len(audioData)):
        tname = audioTitle(audioData, t)
        audioList.append(Choice(f'[{str(t).rjust(2)}]: {tname}', value=t))
    
    if not noVideo:
        audioList.append(Choice('[-1]: No Audio', value='-1'))
    
    if noVideo and len(audioList) < 1:
        return
    
    audioCmd = [ '-an' ]
    audioTrack = questionary.select('Select Audio Track:', audioList).ask()
    if audioTrack != '-1':
        atid = int(audioTrack)
        audioCmd = [ '-map', f'0:a:{atid}?', f'-c:a', 'copy' ]
    
    vTitle = questionary.text('Set Video Title:').ask()
    
    encCmd = list()
    encCmd.extend([ r'ffmpeg', '-hide_banner', ])
    encCmd.extend([ '-loglevel', 'error', '-stats', ])
    encCmd.extend([ '-hwaccel', 'auto', ])
    encCmd.extend([ '-fflags', '+bitexact', '-flags:v', '+bitexact', '-flags:a', '+bitexact' ])
    
    encCmd.extend([ '-i', inFile ]);
    if not noVideo:
        encCmd.extend([ '-map', f'0:v:0?', '-c:v', 'copy' ])
    
    encCmd.extend(audioCmd)
    encCmd.extend([ '-sn', '-dn' ])
    
    encCmd.extend([ '-map_metadata', '-1', '-map_chapters', '-1' ])
    
    if vTitle != '':
        encCmd.extend([ '-metadata:s:v:0', f'title={vTitle}' ])
    
    # encCmd.extend([ '-brand', 'mp42' ])
    encCmd.extend([ outFile ])
    
    startTime = time.monotonic()
    subprocess.run(encCmd)
    
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
    inputPath = input(':: Folder/File: ').strip('\"')
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
            print(f':: Input file is not a video or audio file: {inputPath}')
    elif os.path.isdir(inputPath):
        print(f':: Input Folder: {inputPath}')
        configFolder(inputPath)
    else:
        print(f':: Input path is not a folder, video or audio file: {inputPath}')
except Exception as err:
    print(f':: Something goes wrong...')
    print(f':: {type(err).__name__}: {err}')
    
    import traceback
    tb_exc = traceback.format_tb(err.__traceback__)
    
    for tb_line in tb_exc:
        if not tb_line.startswith(f'  File "<frozen os>"'):
            print(f':: {tb_line.strip()}')

# end
if os.environ.get('isBatch') is None:
    questionary.press_any_key_to_continue(message = '\n:: Press enter to continue...\n').ask()
