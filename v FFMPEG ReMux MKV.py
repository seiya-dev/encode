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
from _encHelper import getMediaData, audioTitle, subsTitle, searchSubsFile

# file
def configFile(inFile: Path):
    outFolder = PurePath(inFile).parent
    outFile   = f'{outFolder}/{PurePath(inFile).stem} [remux].mkv'
    
    videoData = getMediaData(inFile, 'v', True)
    if len(videoData) < 1:
        print()
        print(f':: Skipping: {PurePath(inFile).name}')
        print(f':: No video streams!')
        return
    
    videoInfo = getMediaData(inFile)
    videoDur  = round(float(videoInfo['format']['duration']))
    videoDur_h, videoDur_r = divmod(videoDur, 3600)
    videoDur_m, videoDur_s = divmod(videoDur_r, 60)
    print(f':: Duration : {videoDur_h:02.0f}:{videoDur_m:02.0f}:{videoDur_s:02.0f}')
    
    audioList = list()
    audioData = getMediaData(inFile, 'a')
    for t in range(len(audioData)):
        tname = audioTitle(audioData, t)
        audioList.append(Choice(f'[{str(t).rjust(2)}]: {tname}', value=t))
    audioList.append(Choice('[-1]: No Audio', value='-1'))
    
    audioCmd = [ '-an' ]
    audioTrack = questionary.select('Select Audio Track:', audioList).ask()
    if audioTrack != '-1':
        atid = int(audioTrack)
        audioCmd = [ '-map', f'0:a:{atid}?', f'-c:a', 'copy' ]
    
    subsList = list()
    subsData = getMediaData(inFile, 's')
    for t in range(len(subsData)):
        tname = subsTitle(subsData, t)
        subsList.append(Choice(f'[{str(t).rjust(2)}]: {tname}', value=t))
    subsList.append(Choice('[-1]: No Subs', value='-1'))
    
    subsCmd = [ '-sn' ]
    subsTrack = questionary.select('Select Subs Track:', subsList).ask()
    if subsTrack != '-1':
        stid = int(subsTrack)
        subsCmd = [ '-map', f'0:s:{stid}?', f'-c:s', 'copy' ]
        
        attData = getMediaData(inFile, 't')
        for t in range(len(attData)):
            if 'tags' in attData[t] and 'title' in attData[t]['tags'] and 'mimetype' in attData[t]['tags']:
                tags = attData[t]['tags']
                subsCmd.extend([ f'-map', f'0:t:{t}' ])
                subsCmd.extend([ f'-metadata:s:t:{t}', f'filename={tags['filename']}' ])
                subsCmd.extend([ f'-metadata:s:t:{t}', f'mimetype={tags['mimetype']}' ])
    
    vCutCmd = []
    vCutStart = questionary.text('Cut Start:').ask()
    if vCutStart != '':
        vCutEnd = questionary.text('Cut End:').ask()
        vCutCmd.extend([ vCutStart, vCutEnd ])
    
    vTitle = questionary.text('Set Video Title:').ask()
    
    encCmd = list()
    encCmd.extend([ r'ffmpeg', '-hide_banner', ])
    encCmd.extend([ '-loglevel', 'error', '-stats', ])
    encCmd.extend([ '-hwaccel', 'auto', ])
    encCmd.extend([ '-fflags', '+bitexact', '-flags:v', '+bitexact', '-flags:a', '+bitexact' ])
    
    encCmd.extend([ '-i', inFile ]);
    encCmd.extend([ '-map', f'0:v:0?', '-c:v', 'copy' ])
    
    encCmd.extend(audioCmd)
    encCmd.extend(subsCmd)
    encCmd.extend(['-dn'])
    
    if len(vCutCmd) > 0:
        encCmd.extend([ '-ss', vCutCmd[0], '-to', vCutCmd[1] ])
    
    encCmd.extend([ '-map_metadata', '-1', '-map_chapters', '-1' ])
    
    if vTitle != '':
        encCmd.extend([ '-metadata:s:v:0', f'title={vTitle}' ])
    
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
        if extVideoFile.count(fileExt) > 0:
            print(f':: Input File: {inputPath}')
            configFile(inputPath)
        else:
            print(f':: Input file is not a video file: {inputPath}')
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
