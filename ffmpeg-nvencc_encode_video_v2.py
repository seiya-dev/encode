#!/usr/bin/env python3

# set libs
import sys
import os
import re

import time
import subprocess

import argparse
import json
from pathlib import Path
from pathlib import PurePath

import questionary
from questionary import Choice, Validator, ValidationError, prompt

extFile = ['.mkv', '.mp4', '.mov', '.avs']
reName = re.compile(r'^(?P<title>.+?( \d|\(\d+\))?)( -)? (?P<episode>(\d+|SP( )?(\d+)|OVA( )?(\d+)?)(v\d)?)$')
reClean = re.compile(r'^(\[[^\[\]]*?\]|\([^\(\)]*?\)) | (\[[^\[\]]*?\]|\([^\(\)]*?\))$')

# int validator
def IntValidator(text):
    if len(text) == 0:
        return 'Please enter a value'
    try:
        int(text)
    except ValueError:
        return 'Please enter a value'
    return True

# get data from video file
def getVideoData(inputVideo: Path, streamType: str):
    result = subprocess.run([
        r'ffprobe', '-v', 'error', '-hide_banner',
        '-print_format', 'json', '-show_format', '-show_streams', 
        '-select_streams', streamType,
        inputVideo
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = json.loads(result.stdout.decode('utf-8'))
    return result

# find subs files
def searchSubsFile(inputVideo: Path):
    subsData = argparse.Namespace()
    subsData.root = PurePath(inputVideo).parent
    subsData.prefix = PurePath(inputVideo).stem
    subsData.files = []
    if PurePath(inputVideo).suffix.lower() == '.mkv':
        subsData.files.extend([os.path.join(os.path.sep, subsData.root, PurePath(inputVideo).name)])
    for root, dirs, files in os.walk(subsData.root):
        for file in files:
            if file.startswith(f'{subsData.prefix}') and file.lower().endswith('.ass'):
                subsData.files.append(os.path.join(os.path.sep, root, file))
    return subsData

# fix path for ffmpeg
def fixPath(inFile: Path, forFFmpeg: bool):
    inFile = inFile.replace('\\', '/')
    if forFFmpeg:
        inFile = inFile.replace(':', r'\:')
        if os.name == 'nt':
            inFile = inFile.replace("'", r"'\\\''")
        else:
            inFile = inFile.replace("'", r"'\''")
    return inFile

def encodeFile(inFile: Path, useFFmpeg: bool, audioTrackIndex: int, encodeAudio: bool, subsTrackIndex: int, subsFileIndex: int):
    # inFile  = os.path.abspath(inFile)
    inDir   = PurePath(inFile).parent
    inFonts = fixPath(f'{inDir}/fonts', useFFmpeg)
    inSubs  = searchSubsFile(inFile).files
    
    videoData = getVideoData(inFile, 'v:0')['streams']
    if len(videoData) < 0:
        print(f':: Skipping: {PurePath(inFile).name}')
        return
    
    videoData = videoData[0]
    outVideoSize = [[ str(videoData['width']), 'orig' ]]
    audioBitrate = '192'
    
    if videoData['width'] >= 2560 or videoData['height'] >= 1440:
        outVideoSize.append(['1920', '1080'])
    if videoData['width'] >= 1920 or videoData['height'] >= 1080:
        outVideoSize.append(['1280', '720'])
    
    isGifv = False
    if os.environ.get('toGifv') != None and os.environ.get('toGifv') == '1':
        print('\n:: Convert to GIFV!')
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
            encCmd.extend([ '-c:v', 'libx264', '-crf', '20' ])
            encCmd.extend([ '-preset:v', 'faster', '-tune:v', 'animation' ])
        else:
            encCmd.extend([ r'NVEncC64' ])
            encCmd.extend([ '-i', inFile, '-o', outFile ])
            encCmd.extend([ '--metadata', 'copy', '--chapter-copy' ])
            encCmd.extend([ '--codec', 'h264', '--cqp', '20:23:25', '--preset', 'P3' ])
            encCmd.extend([ '--max-bitrate', '10000', '--lookahead', '32' ])
            encCmd.extend([ '--output-depth', '8' ])
        
        vFilters = '[0:v:0]format=yuv420p'
        overlay = False
        inSubsLog = ''
        
        if len(inSubs) > 0 and subsFileIndex > -1 and subsTrackIndex > -1:
            if subsFileIndex > len(inSubs):
                subsFileIndex = len(inSubs) - 1
            inSubsFile = fixPath(inSubs[subsFileIndex], useFFmpeg)
            inSubsLog  = str(inSubs[subsFileIndex]).replace(f'{str(inDir)}{os.path.sep}', '')
            if useFFmpeg:
                inpSubsStr = f'filename=\'{inSubsFile}\''
                if inSubsFile.lower().endswith('.mkv'):
                    inpSubsStr = inpSubsStr + f':stream_index={subsTrackIndex}'
                    inSubsLog = inSubsLog + f':track={subsTrackIndex}'
                outsubs = f'subtitles={inpSubsStr}:fontsdir=\'{inFonts}\''
                if inSubsFile.lower().endswith('.mkv'):
                    subsData = getVideoData(inFile, f's:{subsTrackIndex}')['streams']
                    if len(subsData) > 0 and subsData[0]['codec_name'] == 'hdmv_pgs_subtitle':
                        vFilters = f'{vFilters}[v];[v][0:s:{subsTrackIndex}]overlay'
                        overlay = True
                        outsubs = ''
                if outsubs:
                    vFilters = f'{vFilters},{outsubs}'
            else:
                inpSubsStr = f'filename="{inSubsFile}"'
                if inSubsFile.lower().endswith('.mkv'):
                    inpSubsStr = f'track={subsTrackIndex + 1}'
                    inSubsLog = inSubsLog + f':track={subsTrackIndex + 1}'
                encCmd.extend([ '--vpp-subburn', f'{inpSubsStr},fontsdir="{inFonts}"' ])
        
        if x > 0:
            byWidth = True if int(curVideoSize[0]) / (videoData['width']/videoData['height']) <= int(curVideoSize[1]) else False
            if useFFmpeg:
                if byWidth:
                    oscale = f'scale={curVideoSize[0]}:-2'
                else:
                    oscale = f'scale=-2:{curVideoSize[1]}'
                oscsep = '[v];[v]' if overlay else ','
                vFilters = f'{vFilters}{oscsep}{oscale}'
            else:
                if byWidth:
                    encCmd.extend([ '--output-res', f'{curVideoSize[0]}x-2' ])
                else:
                    encCmd.extend([ '--output-res', f'-2x{curVideoSize[1]}' ])
        
        if useFFmpeg:
            encCmd.extend([ '-filter_complex', vFilters ])
        
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
        print(f':: Output   : {PurePath(outFile).name}\n')
        
        # print(vFilters)
        # print('\n  '.join(encCmd) + '\n')
        subprocess.call(encCmd)
        
        runTime = time.monotonic() - startTime
        hours, rem = divmod(runTime, 3600)
        minutes, seconds = divmod(rem, 60)
        print(f'\n:: Encoded {PurePath(outFile).name} in {hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}')

# encode
def configEncode(inputPath: Path):
    # filesArr
    inpFile = []
    
    # check if dir
    if os.path.isdir(inputPath):
        for file in os.listdir(inputPath):
            file = os.path.join(inputPath, file)
            fileExt = PurePath(file).suffix.lower()
            if extFile.count(fileExt) > 0:
                inpFile.extend([file])
    
    # file to array
    if os.path.isfile(inputPath):
        inpFile.extend([inputPath])
    
    # check files
    if len(inpFile) < 1:
        print(':: No videos in folder!')
        return
    
    # useNVEnc
    useNVEnc = questionary.confirm('Use NVEnc (default=No):', default=False).ask()
    
    # useFFmpeg
    useFFmpeg = (not useNVEnc)
    
    # get audio data from first video
    audioData = getVideoData(inpFile[0], 'a')['streams']
    
    # show tracks
    print(f'\n:: Audio from first file:')
    if len(audioData) > 0:
        for t in range(len(audioData)):
            a = audioData[t]
            codec = a['codec_name']
            lang = a['tags']['language']
            title = a['tags']['title'] if 'title' in a['tags'] else ''
            print(f'[{t}] {codec} {lang} {title}')
    else:
        print(f'[-] No audio')
    
    # index
    audioTrackIndex = int(questionary.text('Audio track index (no audio: -1):', default='0', validate=IntValidator).ask())
    
    if audioTrackIndex < -1:
        audioTrackIndex = -1
    if audioTrackIndex > 1000:
        audioTrackIndex = 1000
    
    encodeAudio = False
    if audioTrackIndex > -1:
        print('')
        encodeAudio = questionary.confirm('Encode audio (default=No):', default=False).ask()
        print('')
    
    subsData = searchSubsFile(inpFile[0])
    if len(subsData.files) > 0:
        print(f':: Subtitles for first file:')
        for t in range(len(subsData.files)):
            print(f'[{t}] {PurePath(subsData.files[t]).name}')
    
    subsFileDefault = '0' if PurePath(inpFile[0]).suffix.lower() == '.mkv' else '-1'
    subsFileIndex = int(questionary.text('Subtitle file index for hardsubs (-1: Skip):', default=subsFileDefault, validate=IntValidator).ask())
    
    if subsFileIndex < -1:
        subsFileIndex = -1
    if subsFileIndex > 1000:
        subsFileIndex = 1000
    
    subsTrackIndex = 0
    if PurePath(inpFile[0]).suffix.lower() == '.mkv' and subsFileIndex == 0:
        subsData = getVideoData(inpFile[0], 's')['streams']
        print(f'\n:: Subtitles from first file:')
        if len(subsData) > 0:
            for t in range(len(subsData)):
                s = subsData[t]
                lang = s['tags']['language']
                title = s['tags']['title'] if 'title' in s['tags'] else ''
                print(f'[{t}] {lang} {title}')
        else:
            print(f'[-] No subtitles')
        subsTrackIndex = int(questionary.text('Subtitle track index for hardsubs (-1: Skip):', default='0', validate=IntValidator).ask())
        if subsTrackIndex < -1:
            subsTrackIndex = -1
        if subsTrackIndex > 1000:
            subsTrackIndex = 1000
    
    for i in range(len(inpFile)):
        encodeFile(inpFile[i], useFFmpeg, audioTrackIndex, encodeAudio, subsTrackIndex, subsFileIndex)

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
    if extFile.count(fileExt) > 0:
        print(f':: Input file: {inputPath}')
        configEncode(inputPath)
    else:
        print(f':: Input file is not a video file: {inputPath}')
        
elif os.path.isdir(inputPath):
    print(f':: Input folder: {inputPath}')
    configEncode(inputPath)
else:
    print(f':: Input path is not a folder or video file: {inputPath}')


# end
if os.environ.get('isBatch') is None:
    input('\n:: Press enter to continue...\n')
