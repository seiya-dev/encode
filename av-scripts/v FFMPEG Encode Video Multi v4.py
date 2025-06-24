#!/usr/bin/env python3

import os
import re
import sys
import time
import subprocess

from pathlib import Path
from pathlib import PurePath

try:
    from _encHelper import moduleNotFound
    from _encHelper import boolYN, IntValidator, PathValidator, extVideoFile, fixPath
    from _encHelper import getMediaData, audioTitle, searchSubsFile
except ModuleNotFoundError as errorModule:
    print(':: EncHelper Not Found...')
    input(':: Press enter to continue...\n')
    exit()

try:
    from questionary import press_any_key_to_continue as qpause
    from questionary import text as qtext, select as qselect, confirm as qconfirm
    from questionary import Choice, Validator, ValidationError
except ModuleNotFoundError as errorModule:
    moduleNotFound(str(errorModule))
    exit()

#################################################

reName = re.compile(r'^(?P<title>.+?( \d|\(\d+\))?)( -)? (?P<episode>(\d+|SP( )?(\d+)|OVA( )?(\d+)?)(v\d+)?)$')
reClean = re.compile(r'^(\[[^\[\]]*?\]|\([^\(\)]*?\))|(\s?\[[^\[\]]*?\]|\([^\(\)]*?\))+(_rev(\d+)?)?$')

#################################################

# encode
def encodeFile(inFile: Path, nvEncCodec: bool, setQuality: str, doResize: bool, audioTrackIndex: str, encodeAudio: bool, subsTrackIndex: str):
    # inFile  = os.path.abspath(inFile)
    inDir   = PurePath(inFile).parent
    inFonts = fixPath(f'{inDir}/fonts', True)
    inSubs  = searchSubsFile(inFile)
    
    videoData = getMediaData(inFile, 'v', True)
    if len(videoData) < 1:
        print()
        print(f':: Skipping: {PurePath(inFile).name}')
        print(f':: No video streams!')
        return
    
    videoData = videoData[0]
    audioData = getMediaData(inFile, 'a')
    outVideoSize = [[ str(videoData['width']), str(videoData['height']) ]]
    audioBitrate = '192'
    
    if 'display_aspect_ratio' in videoData:
        aspect = videoData['display_aspect_ratio'].split(':')
        aspect = int(aspect[0]) / int(aspect[1])
    else:
        aspect = videoData['width'] / videoData['height']
    aspect = round(aspect, 2)
    
    if doResize:
        if videoData['width'] >= aspect * 1440 - 80 or videoData['height'] >= 1440:
            outVideoSize.append(['1920', '1080'])
        if videoData['width'] >= aspect * 1080 - 80 or videoData['height'] >= 1080:
            outVideoSize.append(['1280', '720'])
    
    for x in range(len(outVideoSize)):
        outFolder = inDir
        outNameTemp = PurePath(inFile).stem
        curVideoSize = outVideoSize[x]
        
        reMatchClean = re.search(reClean, outNameTemp)
        while reMatchClean is not None:
            outNameTemp = (re.sub(reClean, '', outNameTemp)).strip()
            reMatchClean = re.search(reClean, outNameTemp)
        
        outExt = f'{curVideoSize[1]}p'
        if m := reName.match(outNameTemp):
            title, episode = m.group('title'), m.group('episode')
            outFolder = f'{outFolder}/../{title}'
            outFile   = f'{title} - {episode} [{outExt}].mp4'
        else:
            if os.path.isdir(inputPath):
                outFolder = f'{outFolder} [ENCODED]'
            outFile   = f'{PurePath(inFile).stem} [{outExt}].mp4'
        
        os.makedirs(outFolder, exist_ok=True)
        outFile = os.path.abspath(f'{outFolder}/{outFile}')
        
        encCmd = list()
        encCmd.extend([ r'ffmpeg', '-hide_banner', ])
        encCmd.extend([ '-loglevel', 'error', '-stats', ])
        encCmd.extend([ '-hwaccel', 'auto', ])
        encCmd.extend([ '-fflags', '+bitexact' ])
        encCmd.extend([ '-flags:v', '+bitexact' ])
        encCmd.extend([ '-flags:a', '+bitexact' ])
        
        # same as -pix_fmt yuv420p
        vFilters = '[0:v:0]format=yuv420p'
        outsubs = None
        overlay = False
        inSubsLog = ''
        
        if subsTrackIndex != '-1' and subsTrackIndex in inSubs.inf:
            inSubsInf  = inSubs.inf[subsTrackIndex]
            inSubsFile = fixPath(inSubsInf['file'], True)
            inSubsLog  = inSubsInf['title']
            tid        = int(subsTrackIndex.split(':')[1])
            
            if not inSubsInf['ext']:
                inSubsLog = f'[0:{tid}] {inSubsLog}'
            
            outsubs = f'filename=\'{inSubsFile}\''
            if inSubsInf['ext']:
                outsubs = f'subtitles={outsubs}:fontsdir=\'{inFonts}\''
            else:
                subsCodec = inSubsInf['codec']
                if subsCodec == 'dvd_subtitle' or subsCodec == 'hdmv_pgs_subtitle':
                    overlay = True
                    outsubs = f'[v];[v][0:s:{tid}]overlay'
                else:
                    outsubs = f'subtitles={outsubs}:stream_index={tid}:fontsdir=\'{inFonts}\''
            comaadd = ',' if not overlay else ''
            vFilters = f'{vFilters}{comaadd}{outsubs}'
        
        cVS = curVideoSize
        vDS = videoData['width'] / videoData['height']
        
        if cVS[0].isdigit() and cVS[1].isdigit():
            byWidth = True if int(cVS[0]) / vDS <= int(cVS[1]) else False
            oscale = f'scale={cVS[0]}:-2' if byWidth else f'scale=-2:{cVS[1]}'
            oscsep = '[v];[v]' if overlay else ','
            vFilters = f'{vFilters}{oscsep}{oscale}'
        
        audioCmd = list()
        extAudio = list()
        outAudio = ''
        
        if audioTrackIndex != '-1':
            atrack = audioTrackIndex.split(':')
            if len(audioData) > 0 and atrack[0] == '0':
                outAudio += f'[{audioTrackIndex}] {audioTitle(audioData, int(atrack[1]))}'
                audioCmd.extend([ '-map', f'{atrack[0]}:a:{atrack[1]}?', f'-c:a' ])
                if encodeAudio:
                    outAudio += f' -> aac 2ch {audioBitrate}k'
                    audioCmd.extend([ 'aac', '-cutoff', '0', '-b:a', f'{audioBitrate}k', '-ac', '2' ])
                else:
                    outAudio += f' -> copy'
                    audioCmd.extend([ 'copy' ])
        
        encCmd.extend([ '-i', inFile ]);
        if audioTrackIndex == '-1' or len(extAudio) > 0:
            encCmd.extend([ '-an' ])
        encCmd.extend([ '-sn', '-dn' ])
        
        encCmd.extend([ '-filter_complex', f'{vFilters}[video]' ])
        
        vcodec   = 'h264_nvenc' if nvEncCodec else 'libx264'
        vpreset  = 'p2'         if nvEncCodec else 'faster'
        vencmode = '-cq'        if nvEncCodec else '-crf'
        vtune    = 'hq'         if nvEncCodec else 'animation'
        vqual    = setQuality
        
        encCmd.extend([ '-map', '[video]', '-c:v', vcodec, vencmode, vqual ])
        encCmd.extend([ '-preset:v', vpreset, '-tune:v', vtune ])
        if outAudio != '':
            encCmd.extend(audioCmd)
        
        # output
        # https://github.com/rodrigopolo/cheatsheets/blob/master/ffmpeg.md
        encCmd.extend([ '-map_metadata', '-1', '-map_chapters', '-1' ])
        encCmd.extend([ '-metadata', 'application=' ])
        encCmd.extend([ '-metadata', 'writing_library=' ])
        encCmd.extend([ '-metadata:s:v:0', 'title=CyTube Encoders' ])
        # encCmd.extend([ '-brand', 'mp42' ])
        encCmd.extend([ outFile ])
        
        videoInfo = getMediaData(inFile)
        videoDur  = round(float(videoInfo['format']['duration']))
        videoDur_h, videoDur_r = divmod(videoDur, 3600)
        videoDur_m, videoDur_s = divmod(videoDur_r, 60)
        
        startTime = time.monotonic()
        vDurStr = f'{videoDur_h:02.0f}:{videoDur_m:02.0f}:{videoDur_s:02.0f}'
        print(f'\n:: Encoding : [{vDurStr}] {PurePath(inFile).name}')
        print(f':: Audio    : {outAudio}')
        if inSubsLog != '':
            print(f':: Subtitles: {inSubsLog}')
        print(f':: Output   : {PurePath(outFile).name}\n')
        
        testRun = False
        if testRun:
            print(encCmd)
            print('OK')
        
        if not testRun and curVideoSize[0].isdigit() and curVideoSize[1].isdigit():
            subprocess.run(encCmd)
        
        runTime = time.monotonic() - startTime
        hours, rem = divmod(runTime, 3600)
        minutes, seconds = divmod(rem, 60)
        print(f'\n:: Encoded {PurePath(outFile).name} in {hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}')

# config
def configEncode(inPath: Path):
    # filesArr
    inFiles = list()
    
    # check if dir
    if os.path.isdir(inPath):
        for file in os.listdir(inPath):
            file = os.path.join(inPath, file)
            fileExt = PurePath(file).suffix.lower()
            if extVideoFile.count(fileExt) > 0:
                inFiles.append(file)
    
    # file to array
    if os.path.isfile(inPath):
        inFiles.append(inPath)
    
    # check files
    if len(inFiles) < 1:
        print(':: No input videos!')
        return
    
    # useNVEnc
    nvEncCodec = qconfirm('Use NVEnc Codec (Default=No):', default=False).ask()
    
    vqType = 'CQ' if nvEncCodec else 'CRF'
    vqual  = '25' if nvEncCodec else '20'
    setQuality = qtext(f'Set Encode {vqType}:', validate=IntValidator, default=vqual).ask()
    
    # ask resizes
    doResize = qconfirm('Do Multiply Qualities (Default=Yes):', default=True).ask()
    
    audioList = list()
    audioData = getMediaData(inFiles[0], 'a')
    for t in range(len(audioData)):
        tname = audioTitle(audioData, t)
        audioList.append(Choice(f'[0:{t}]: {tname}', value=f'0:{t}'))
    
    audioList.append(Choice('[-1]: No Audio', value='-1'))
    audioTrackIndex = qselect('Select Audio Track:', audioList).ask()
    
    encodeAudio = False
    if audioTrackIndex != '-1':
        encodeAudio = qconfirm('Encode Audio to AAC 192k 2ch (Default=No):', default=False).ask()
    
    subsData = searchSubsFile(inFiles[0])
    subsTrackIndex = qselect('Subtitle For HardSubs:', subsData.sel).ask()
    
    for inFile in inFiles:
        encodeFile(inFile, nvEncCodec, setQuality, doResize, audioTrackIndex, encodeAudio, subsTrackIndex)

# set folder
if len(sys.argv) < 2:
    inputPath = qtext(':: Folder/File: ', validate=PathValidator).ask()
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
            configEncode(inputPath)
        else:
            print(f':: Input file is not a video file: {inputPath}')
    elif os.path.isdir(inputPath):
        print(f':: Input Folder: {inputPath}')
        configEncode(inputPath)
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
    qpause(message = '\n:: Press enter to continue...\n').ask()
