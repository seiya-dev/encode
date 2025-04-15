#!/usr/bin/env python3

import os
import re
import sys
import time
import shutil
import struct
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

from _encHelper import boolYN, IntValidator, FloatValidatorP, PathValidator, extVideoFile, fixPath
from _encHelper import getMediaData, audioTitle, searchSubsFile
extVideoFile.extend(['.gif'])

def videoFilterGen(extendedFilter: bool = False):
    baseFilter = "[0:v:0]scale=512:512:force_original_aspect_ratio=decrease"
    
    if not extendedFilter:
        return baseFilter
    
    rgbVal = f"r='r(X,Y)':g='g(X,Y)':b='b(X,Y)'"
    rv = "25"
    
    alphaMask = (
        f":a='255"
        f"* max(lt(hypot(  X-{rv},   Y-{rv}), {rv}), 1-lt(X,   {rv})*lt(Y,   {rv}))"
        f"* max(lt(hypot(W-X-{rv},   Y-{rv}), {rv}), 1-gt(X, W-{rv})*lt(Y,   {rv}))"
        f"* max(lt(hypot(  X-{rv}, H-Y-{rv}), {rv}), 1-lt(X,   {rv})*gt(Y, H-{rv}))"
        f"* max(lt(hypot(W-X-{rv}, H-Y-{rv}), {rv}), 1-gt(X, W-{rv})*gt(Y, H-{rv}))'"
    )
    
    extFilter = (
        f"{baseFilter},format=rgba[v];"
        f"[v]geq={rgbVal}{alphaMask}[v];"
        f"[v]format=yuva420p"
    )
    
    return extFilter

# file
def configFile(inFile: Path):
    videoData = getMediaData(inFile, 'v', True)
    if len(videoData) < 1:
        print()
        print(f':: Skipping: {PurePath(inFile).name}')
        print(f':: No video streams!')
        return
    
    # customs
    encFPS = ''
    encTrm = ''
    
    useOvl = questionary.confirm('Use Overlay Filter (Default=No):', default=False).ask()
    encCrf = questionary.text('Set Encode CRF:', validate=IntValidator, default='20').ask()
    # encFPS = questionary.text('Set Custom FPS:', default='').ask()
    # encTrm = questionary.text('Trim Video:', default='').ask()
    vTitle = questionary.text('Set Video Title:').ask()
    
    startTime = time.monotonic()
    encodeTgSticker(inFile, useOvl, encCrf, encFPS, encTrm, vTitle)
    
    runTime = time.monotonic() - startTime
    hours, rem = divmod(runTime, 3600)
    minutes, seconds = divmod(rem, 60)
    print(f'\n:: Encoded {PurePath(inFile).name} in {hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}')

def encodeTgSticker(inFile: Path, useOvl: bool, encCrf: int, encFPS: str, encTrm: str, vTitle: str, isRetry: bool = False):
    outFolder = PurePath(inFile).parent
    outFile   = f'{outFolder}/{PurePath(inFile).stem} [tg crf-{encCrf}].webm'
    outFileFx = f'{outFolder}/{PurePath(inFile).stem} [tg crf-{encCrf}-fix].webm'
    outFilter = videoFilterGen(useOvl)
    
    encCmd = list()
    encCmd.extend([ r'ffmpeg', '-hide_banner', ])
    encCmd.extend([ '-loglevel', 'error', '-stats', ])
    encCmd.extend([ '-hwaccel', 'auto', ])
    encCmd.extend([ '-fflags', '+bitexact' ])
    encCmd.extend([ '-flags:v', '+bitexact' ])
    encCmd.extend([ '-flags:a', '+bitexact' ])
    
    encCmd.extend([ '-i', inFile ]);
    encCmd.extend([ '-an', '-sn', '-dn' ])
    
    encCmd.extend([ '-filter_complex', f'{outFilter}[video]' ])
    encCmd.extend([ '-map', '[video]', '-c:v', 'libvpx-vp9', '-b:v', '0' ])
    encCmd.extend([ '-crf', f'{encCrf}', '-deadline', 'best' ])
    encCmd.extend([ '-map_metadata', '-1', '-map_chapters', '-1' ])
    
    encCmd.extend([ '-metadata', 'application=' ])
    encCmd.extend([ '-metadata', 'writing_library=' ])
    
    if vTitle != '':
        encCmd.extend([ '-metadata:s:v:0', f'title={vTitle}' ])
    
    if FloatValidatorP(encFPS):
        encCmd.extend([ '-r', encFPS ])
        if not filterTest:
            print(f':: FPS Changed to {encFPS}')
    
    if FloatValidatorP(encTrm):
        encCmd.extend([ '-t', encTrm ])
        if not filterTest:
            print(f':: Trimmed to {encTrm}')
    
    print(f':: Trying Encode File With CRF {encCrf}')
    encCmd.extend([ outFile ])
    
    if not os.path.isfile(outFile):
        subprocess.run(encCmd)
    
    fsize = os.path.getsize(outFile)
    if fsize > 256*1024 and int(encCrf) < 63:
        # os.remove(outFile)
        outFile, outFileFx = encodeTgSticker(inFile, useOvl, int(encCrf)+1, encFPS, encTrm, vTitle, True)
    
    if isRetry:
        return outFile, outFileFx
    
    if not os.path.isfile(outFileFx):
        stickData = getMediaData(outFile)
        if 'format' in stickData and 'duration' in stickData['format']:
            if float(stickData['format']['duration']) > 3:
                shutil.copy(outFile, outFileFx)
                
                file = open(outFileFx, 'r+b')
                content = file.read()
                offset = content.find(b'\x44\x89')
                
                if offset > -1:
                    file.seek(offset + 2)
                    elSize = file.read(1)
                    if elSize == b'\x88':
                        # 8 bytes double float
                        file.write(struct.pack('>d', 3000))

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
    print(f'\n:: Something goes wrong...')
    print(f':: {type(err).__name__}: {err}')
    
    import traceback
    tb_exc = traceback.format_tb(err.__traceback__)
    
    for tb_line in tb_exc:
        if not tb_line.startswith(f'  File "<frozen os>"'):
            print(f':: {tb_line.strip()}')

# end
if os.environ.get('isBatch') is None:
    questionary.press_any_key_to_continue(message = '\n:: Press enter to continue...\n').ask()
