#!/usr/bin/env python3

# set libs
import sys
import os
import re

import time
import subprocess

from pathlib import Path
from pathlib import PurePath

reName = re.compile(r'^(?P<title>.+?( \d|\(\d+\))?)( -)? (?P<episode>(\d+|SP( )?(\d+)|OVA( )?(\d+)?)(v\d)?)$')
reClean = re.compile(r'^(\[[^\[\]]*?\]|\([^\(\)]*?\)) | (\[[^\[\]]*?\]|\([^\(\)]*?\))$')

def checkYN(inputStr: str):
    inputStr = str(inputStr).lower().strip()
    if len(inputStr) > 0 and inputStr[0] == 'y':
        return True
    else:
        return False

def askYN(question: str):
    ask = input(f'{question}(y/N) ')
    return checkYN(ask)

def getVideoSize(inputVideoFile: Path):
    result = subprocess.run([
        r'ffprobe', '-v', 'error', '-hide_banner',
        '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
        '-of', 'default=noprint_wrappers=1:nokey=1', inputVideoFile
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = result.stdout.decode('utf-8').replace(r'\r\n', r'\n')
    return list(map(int, result.splitlines()[-2:]))

def fixPath(inFile: Path, forFFmpeg: bool):
    inFile = inFile.replace('\\', '/')
    if forFFmpeg:
        inFile = inFile.replace(':', r'\:')
        if os.name == 'nt':
            inFile = inFile.replace("'", r"'\\\''")
        else:
            inFile = inFile.replace("'", r"'\''")
    return inFile

## process file
def encodeFile(inFile: Path, useFFmpeg: bool, audioTrackIndex: int, encodeAudio: bool, subsTrackIndex: int, subsFileIndex: int):
    inFile  = os.path.abspath(inFile)
    inDir   = PurePath(inFile).parent
    inFonts = fixPath(f'{inDir}/fonts', useFFmpeg)
    inSubs  = []
    
    if PurePath(inFile).suffix.lower() == '.mkv':
        inSubs.append(inFile)
    
    for root, dirs, files in os.walk(inDir):
        for file in files:
            if file.startswith(f'{PurePath(inFile).stem}') and file.lower().endswith('.ass'):
                inSubs.append(os.path.join(os.path.sep, root, file))
    
    srcVideoSize = getVideoSize(inFile)
    outVideoSize = [[ str(srcVideoSize[0]), 'orig' ]]
    audioBitrate = '192'
    
    # if srcVideoSize[0] >= 7680 or srcVideoSize[1] >= 4320:
    #     outVideoSize.append(['3840', '2160'])
    # 
    # if srcVideoSize[0] >= 3840 or srcVideoSize[1] >= 2160:
    #     outVideoSize.append(['2560', '1440'])
    
    if srcVideoSize[0] >= 2560 or srcVideoSize[1] >= 1440:
        outVideoSize.append(['1920', '1080'])
    
    if srcVideoSize[0] >= 1920 or srcVideoSize[1] >= 1080:
        outVideoSize.append(['1280', '720'])
    
    isGifv = False
    if os.environ.get('toGifv') != None and os.environ.get('toGifv') == '1':
        print(':: Convert to GIFV!')
        outVideoSize = [[]]
        outVideoSize.append([ '512', '512' ])
        outVideoSize.append([ '848', '480' ])
        isGifv = True
    
    for x in range(len(outVideoSize)):
        if isGifv and x < 1:
            continue
        
        outFolder = inDir
        outNameTemp = PurePath(inFile).stem
        curVideoSize = outVideoSize[x]
        
        reMatchClean = re.search(reClean, outNameTemp)
        while reMatchClean is not None:
            outNameTemp = re.sub(reClean, '', outNameTemp)
            reMatchClean = re.search(reClean, outNameTemp)
        
        # if m := reName.match(outNameTemp):
        #     title, episode = m.group('title'), m.group('episode')
        #     print(f'{title} - {episode}')
        #     input()
        # print(outNameTemp)
        
        if m := reName.match(outNameTemp):
            title, episode = m.group('title'), m.group('episode')
            outFolder = f'{outFolder}/{title}'
            outFile   = f'{title} - {episode} [{curVideoSize[1]}].mp4'
        else:
            outFolder = f'{outFolder}'
            outExt    = f'{curVideoSize[1]}'
            outFile   = f'{PurePath(inFile).stem}-{outExt}-enc.mp4'
        
        os.makedirs(outFolder, exist_ok=True)
        outFile = os.path.abspath(f'{outFolder}/{outFile}')
        
        encCmd = []
        
        if useFFmpeg:
            encCmd.extend([ r'ffmpeg', '-hide_banner' ])
            encCmd.extend([ '-i', inFile ]);
            encCmd.extend([ '-map_metadata', '-1', '-map_chapters', '-1' ])
            encCmd.extend([ '-map', '0:v:0', '-c:v', 'libx264', '-crf', '20' ])
            encCmd.extend([ '-preset:v', 'faster', '-tune:v', 'animation' ])
        else:
            encCmd.extend([ r'NVEncC64' ])
            encCmd.extend([ '-i', inFile, '-o', outFile ])
            encCmd.extend([ '--metadata', 'copy', '--chapter-copy' ])
            encCmd.extend([ '--codec', 'h264', '--cqp', '20:23:25', '--preset', 'P3' ])
            encCmd.extend([ '--max-bitrate', '10000', '--lookahead', '32' ])
            encCmd.extend([ '--output-depth', '8' ])
        
        vFilters = [ 'format=yuv420p' ]
        inSubsLog = ''
        
        if len(inSubs) > 0 and subsTrackIndex > -1 and subsFileIndex > -1:
            if subsFileIndex > len(inSubs):
                subsFileIndex = len(inSubs) - 1
            inSubsFile = fixPath(inSubs[subsFileIndex], useFFmpeg)
            inSubsLog  = str(inSubs[subsFileIndex]).replace(f'{str(inDir)}{os.path.sep}', '')
            if useFFmpeg:
                inpSubsStr = f'filename=\'{inSubsFile}\''
                if inSubsFile.lower().endswith('.mkv'):
                    inpSubsStr = inpSubsStr + f':stream_index={subsTrackIndex}'
                    inSubsLog = inSubsLog + f':track={subsTrackIndex}'
                vFilters.append(f'subtitles={inpSubsStr}:fontsdir=\'{inFonts}\'')
            else:
                inpSubsStr = f'filename="{inSubsFile}"'
                if inSubsFile.lower().endswith('.mkv'):
                    inpSubsStr = f'track={subsTrackIndex + 1}'
                    inSubsLog = inSubsLog + f':track={subsTrackIndex + 1}'
                encCmd.extend([ '--vpp-subburn', f'{inpSubsStr},fontsdir="{inFonts}"' ])
        
        if x > 0:
            byWidth = True if int(curVideoSize[0]) / (srcVideoSize[0]/srcVideoSize[1]) <= int(curVideoSize[1]) else False
            if useFFmpeg:
                if byWidth:
                    vFilters.append(f'scale={curVideoSize[0]}:-2')
                else:
                    vFilters.append(f'scale=-2:{curVideoSize[1]}')
            else:
                if byWidth:
                    encCmd.extend([ '--output-res', f'{curVideoSize[0]}x-2' ])
                else:
                    encCmd.extend([ '--output-res', f'-2x{curVideoSize[1]}' ])
        
        if useFFmpeg:
            encCmd.extend([ '-vf', ','.join(vFilters) ])
        
        if audioTrackIndex > -1:
            if useFFmpeg:
                encCmd.extend([ '-map', f'0:a:{audioTrackIndex}?', f'-c:a:{audioTrackIndex}' ])
                if encodeAudio:
                    encCmd.extend([ 'aac', '-cutoff', '0', '-b:a', f'{audioBitrate}k', '-ac', '2' ])
                else:
                    encCmd.extend([ 'copy' ])
            else:
                audioTrackNumber = audioTrackIndex + 1
                if encodeAudio:
                    encCmd.extend([ '--audio-codec',   f'{audioTrackNumber}?aac' ])
                    encCmd.extend([ '--audio-bitrate', f'{audioTrackNumber}?{audioBitrate}' ])
                    encCmd.extend([ '--audio-stream',  f'{audioTrackNumber}?:stereo' ])
                else:
                    encCmd.extend([ '--audio-copy', str(audioTrackNumber) ])
        else:
            if useFFmpeg:
                encCmd.extend([ '-an' ])
        
        if useFFmpeg:
            encCmd.extend([ '-sn', outFile ])
        
        if not useFFmpeg and os.path.isfile(outFile):
            nvOw = askYN(f'\n:: "{PurePath(outFile).name}" already exists! Overwrite? ')
            if not nvOw:
                continue
        
        startTime = time.monotonic()
        print(f'\n:: Encoding : {PurePath(inFile).name}')
        if inSubsLog != '':
            print(f':: Subtitles: {inSubsLog}')
        print(  f':: Output   : {PurePath(outFile).name}\n')
        
        # print(vFilters)
        # print('\n  '.join(encCmd) + '\n')
        subprocess.call(encCmd)
        
        runTime = time.monotonic() - startTime
        hours, rem = divmod(runTime, 3600)
        minutes, seconds = divmod(rem, 60)
        print(f'\n:: Encoded {PurePath(outFile).name} in {hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}')

# encode
def configEncode(inputPath: Path):
    print(f':: Selected path: {inputPath}\n')
    fileExt = PurePath(inputPath).suffix.lower()
    
    # useNVEnc
    if os.environ.get('useNVEnc') != None:
        useNVEnc = checkYN(os.environ.get('useNVEnc'))
    else:
        useNVEnc = askYN(':: Use NVEnc? ')
    
    # useFFmpeg
    useFFmpeg = (not useNVEnc)
    
    # audioTrackIndex
    if os.environ.get('audioTrackIndex') != None:
        audioTrackIndex = os.environ.get('audioTrackIndex')
    else:
        audioTrackIndex = input(':: Audio track index (-1: no audio): ')
    
    try:
        audioTrackIndex = int(audioTrackIndex)
    except ValueError:
        audioTrackIndex = 0
    
    if audioTrackIndex < -1:
        audioTrackIndex = -1
    
    if audioTrackIndex > 1000:
        audioTrackIndex = 1000
    
    # encodeAudio
    if audioTrackIndex > -1:
        if os.environ.get('encodeAudio') != None:
            encodeAudio = checkYN(os.environ.get('encodeAudio'))
        else:
            encodeAudio = askYN(':: Encode audio? ')
    else:
        encodeAudio = False
    
    # subsTrackIndex
    if fileExt != '.mp4' and fileExt != '.avs':
        if os.environ.get('subsTrackIndex') != None:
            subsTrackIndex = os.environ.get('subsTrackIndex')
        else:
            subsTrackIndex = input(':: Subtitle track index for hardsubs (-1: Skip): ')
    else:
        subsTrackIndex = 0
    
    try:
        subsTrackIndex = int(subsTrackIndex)
    except ValueError:
        subsTrackIndex = 0
    
    if subsTrackIndex < -1:
        subsTrackIndex = -1
    
    # subsFileIndex
    if os.environ.get('subsFileIndex') != None:
        subsFileIndex = os.environ.get('subsFileIndex')
    else:
        subsFileIndex = input(':: Subtitle file index for hardsubs (-1: Skip): ')
    
    try:
        subsFileIndex = int(subsFileIndex)
    except ValueError:
        if fileExt == '.mkv':
            subsFileIndex = 0
        else:
            subsFileIndex = -1
    
    if subsFileIndex < -1:
        subsFileIndex = -1
    
    if os.path.isfile(inputPath):
        encodeFile(inputPath, useFFmpeg, audioTrackIndex, encodeAudio, subsTrackIndex, subsFileIndex)
    
    if os.path.isdir(inputPath):
        for file in os.listdir(inputPath):
            file = os.path.join(inputPath, file)
            fileLow = file.lower()
            if fileLow.endswith('.mkv') or fileLow.endswith('.mp4') or fileLow.endswith('.avs'):
                encodeFile(file, useFFmpeg, audioTrackIndex, encodeAudio, subsTrackIndex, subsFileIndex)

# set folder
if len(sys.argv) < 2:
    inputPath = input(':: Folder/File: ')
else:
    inputPath = sys.argv[1]

# to abs path
inputPath = os.path.abspath(inputPath)

# check path
if os.path.isfile(inputPath):
    fileExt = PurePath(inputPath).suffix.lower()
    if fileExt == '.mkv' or fileExt == '.mp4' or fileExt == '.avs':
        configEncode(inputPath)
    else:
         print(f':: Path is not a video file: "{inputPath}"!')
elif os.path.isdir(inputPath):
    configEncode(inputPath)
else:
    print(f':: Path is not a folder or video file: "{inputPath}"!')

# end
if os.environ.get('isBatch') is None:
    input('\n:: Press enter to continue...\n')
