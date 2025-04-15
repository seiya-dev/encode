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
    from questionary import Choice, Separator, Validator, ValidationError
except ModuleNotFoundError:
    print(':: Please install "questionary" module: pip install questionary')
    input(':: Press enter to continue...\n')
    exit()

from _encHelper import PathValidator
from _encHelper import getMediaData, audioTitle, searchSubsFile

# acceptable extensions
extVideoFile = ['.mkv', '.mp4', '.avi']
extSubsFile = ['.ass', '.srt']

# encode
# doEncode(inFile, pspEncoderMode, pspEncoderQuality, anamorphMode, videoPar, audioTrack, encAudio, subsTrack)
def doEncode(inFile: Path, pspEncoderMode: int, pspEncoderQuality: str,
    anamorphMode: bool, videoPar: str, audioTrack: str, encAudio: bool, subsTrack: str):
    workFolder = f'{PurePath(inFile).parent}'
    
    tempFolder = os.path.join(workFolder, '_temp')
    pspFolder = os.path.join(workFolder, 'PSP Video')
    
    fontsFolder = os.path.join(workFolder, 'fonts')
    inSubs = searchSubsFile(f'{inFile}i', extSubsFile)
    
    videoData = getMediaData(inFile, 'v')
    if len(videoData) < 1:
        print()
        print(f':: Skipping: {PurePath(inFile).name}')
        print(f':: No video streams!')
        return
    
    os.environ['_cachePath'] = os.path.join(tempFolder, PurePath(inFile).name)
    os.environ['_inputFile'] = inFile
    
    os.environ['_subsFile'] = ''
    os.environ['_fontsDir'] = fontsFolder
    
    os.environ['_avsOutput']  = 'video'
    os.environ['_pspEncMode'] = str(pspEncoderMode)
    os.environ['_pspAnamorph'] = str(pspEncoderMode - 2) if anamorphMode else '0'
    
    os.environ['_outFile'] = str(os.path.join(pspFolder, f'{PurePath(inFile).stem} [PSP]'))
    
    if subsTrack != '-1':
        subsData = inSubs.inf[subsTrack]
        os.environ['_subsFile'] = subsData['file']
    
    encCmd = list()
    encCmd.extend([ r'ffmpeg', '-hide_banner', ])
    encCmd.extend([ '-loglevel', 'error', '-stats', ])
    encCmd.extend([ '-hwaccel', 'auto', ])
    encCmd.extend([ '-fflags', '+bitexact' ])
    encCmd.extend([ '-flags:v', '+bitexact' ])
    encCmd.extend([ '-flags:a', '+bitexact' ])
    
    x264Params = list()
    vSar = ''
    
    if videoPar not in ('1:1', 'auto'):
        vSar = f':sar={videoPar}'
    
    if pspEncoderQuality == 'd':
        x264DefParam = (
            f'deblock=1:-1:keyint=240:min-keyint=1:bframes=3:b-adapt=2:b-pyramid=none:ref=3'
            f':qpmin=15:qpmax=22:ipratio=1.35:pbratio=1.25:vbv-bufsize=10000:vbv-maxrate=10000:qcomp=0.75'
            f':rc-lookahead=120:aq-strength=1.0:me=umh:direct=temporal:subme=9:partitions=p8x8,p4x4,b8x8,i4x4'
            f':trellis=2:aud:nal-hrd=vbr:non-deterministic{vSar}'
        )
        x264Params.extend(['-c:v', 'libx264', '-pix_fmt', 'yuv420p'])
        x264Params.extend(['-profile:v', 'main', '-level:v', '3.0', '-tune:v', 'animation'])
        x264Params.extend(['-preset:v', 'medium', '-crf', '22'])
        # x264Params.extend(['-x264-params', x264DefParam])
    
    if pspEncoderQuality == 'v':
        x264DefParam = f'b-pyramid=none:vbv-bufsize=10000:vbv-maxrate=10000{vSar}'
        x264Params.extend(['-c:v', 'libx264', '-pix_fmt', 'yuv420p'])
        x264Params.extend(['-profile:v', 'main', '-level:v', '3.0', '-tune:v', 'animation'])
        x264Params.extend(['-preset:v', 'veryfast', '-b:v', '512k'])
        # x264Params.extend(['-x264-params', x264DefParam])
    
    if pspEncoderQuality == 's':
        x264DefParam = f'b-pyramid=none:vbv-bufsize=10000:vbv-maxrate=10000{vSar}'
        x264Params.extend(['-c:v', 'libx264', '-pix_fmt', 'yuv420p'])
        x264Params.extend(['-profile:v', 'main', '-level:v', '3.0', '-tune:v', 'animation'])
        x264Params.extend(['-preset:v', 'superfast', '-b:v', '512k'])
        # x264Params.extend(['-x264-params', x264DefParam])
    
    encCmd.extend([ '-i', ])
    encCmd.extend([ os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'avs-templates',
        'psp-encode.avs',
    )])
    
    encCmd.extend([ '-i', ])
    encCmd.extend([ inFile ])
    
    encCmd.extend([ '-map', '0:v:0' ])
    encCmd.extend(x264Params)
    
    audioCmd = list()
    atrack = audioTrack.split(':')
    audioCmd.extend([ '-map', f'1:a:{atrack[1]}?', f'-c:a' ])
    if encAudio:
        audioCmd.extend([ 'aac', '-cutoff', '0', '-b:a', f'192k', '-ac', '2' ])
    else:
        audioCmd.extend([ 'copy' ])
    
    encCmd.extend(audioCmd)
    encCmd.extend([ '-map_metadata', '-1', '-map_chapters', '-1' ])
    encCmd.extend([ f'{os.environ['_outFile']}.mp4' ])
    
    startTime = time.monotonic()
    subprocess.run(encCmd)
    
    runTime = time.monotonic() - startTime
    hours, rem = divmod(runTime, 3600)
    minutes, seconds = divmod(rem, 60)
    print(f'\n:: Encoded {PurePath(os.environ['_outFile']).name} in {hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}')

# folder
def configEncoder(inPath: Path):
    subDirsPath = inPath
    
    if os.path.isfile(inPath):
        subDirsPath = os.path.abspath(str(os.path.dirname(subDirsPath))))
    
    subDirsPath = str(subDirsPath)
    pspDir  = f'{os.path.abspath(subDirsPath)}/PSP Video'
    tempDir = f'{os.path.abspath(subDirsPath)}/_temp'
    
    print(f'\n:: Selected Path: {os.path.abspath(inPath)}')
    
    pspEncoderMode = questionary.select(
        'PSP Encoder Mode:', choices = [
        Choice('[1] VideoSize:[480x272] SAR:[16:9|any] Anamorphic:[No]',  value=1),
        Choice('[2] VideoSize:[640x480] SAR:[4:3]      Anamorphic:[Yes]', value=2),
        Choice('[3] VideoSize:[720x480] SAR:[3:2]      Anamorphic:[Yes]', value=3),
        Choice('[4] VideoSize:[720x576] SAR:[16:9|5:4] Anamorphic:[Yes]', value=4),
        Separator(),
        # Choice('[5] Make Video Thumbs   SAR:[4:3]      Anamorphic:[No]',  value=5),
        # Separator(),
        Choice('[#] CLOSE', value=-1),
    ]).ask()
    
    if pspEncoderMode < 0:
        return 1
    
    inFiles = list()
    if os.path.isdir(inPath):
        for file in os.listdir(inPath):
            file = os.path.join(inPath, file)
            fileExt = PurePath(file).suffix.lower()
            if extVideoFile.count(fileExt) > 0:
                inFiles.append(file)
    if os.path.isfile(inPath):
        inFiles.append(inPath)
    
    if len(inFiles) > 0:
        if not os.path.exists(pspDir):
            os.makedirs(pspDir)
        if not os.path.exists(tempDir):
            os.makedirs(tempDir)
    else:
        print(':: No Input Files')
        return 1
    
    if pspEncoderMode != 5:
        pspEncoderQuality = questionary.select(
            'Select Quality/Encode Speed:', choices = [
            Choice('[D] Excellent Quality / Slow Speed', value='d'),
            Choice('[V] Good Quality / Normal Speed',    value='v'),
            Choice('[S] Standard Quality / Best Speed',  value='s'),
        ]).ask()
        
        anamorphMode = False
        videoPar = '1:1'
        
        if [2, 3, 4].count(pspEncoderMode) > 0:
            anamorphMode = questionary.confirm('Anamorphic Encode? (Default=No) [EXPEREMENTAL]', default=False).ask()
            
            if anamorphMode:
                sarModeData = {
                    '1:1':    { '2': '1:1',  '3':'1:1',   '4':'1:1'   },
                    '4:3':    { '2': '1:1',  '3':'9:8',   '4':'16:15' },
                    '16:9':   { '2': '4:3',  '3':'32:27', '4':'64:45' },
                    '2.40:1': { '2': 'auto', '3':'auto',  '4':'auto'  },
                }
                
                sarOptions = list()
                for sarItem in list(sarModeData.keys()):
                    sarIndex = len(sarOptions)
                    sarOptionValue = '1:1'
                    if sarIndex > 0 or sarIndex < 3:
                        sarOptionValue = sarModeData[str(sarIndex)][str(pspEncoderMode)]
                    sarOptions.append(Choice(f'{sarIndex}={sarItem}',  value=sarOptionValue))
                videoPar = questionary.select('Select SAR:', choices = sarOptions).ask()
        
        audioList = list()
        audioDict = dict()
        audioData = getMediaData(inFiles[0], 'a')
        
        if len(audioData) < 0:
            print(':: Error: No Audio Tracks Available!')
            return 1
        
        for t in range(len(audioData)):
            tname = audioTitle(audioData, t)
            audioDict[f'0:{t}'] = audioData[t]
            audioList.append(Choice(f'[0:{t}]: {tname}', value=f'0:{t}'))
        
        # audioList.append(Choice('[-1]: No Audio', value='-1'))
        audioTrack = questionary.select('Select Audio Track:', audioList).ask()
        
        encAudio = False
        if audioTrack != '-1':
            a = audioDict[audioTrack]
            codec = a['codec_name'] if 'codec_name' in a else 'UNK_CODEC'
            channels = a['channels'] if 'channels' in a else 5+1
            if codec != 'aac':
                encAudio = True
            if channels > 2:
                encAudio = True
        
        subsData = searchSubsFile(f'{inFiles[0]}i', extSubsFile)
        subsTrack = questionary.select('Subtitle For HardSubs:', subsData.sel).ask()
        
        for inFile in inFiles:
            doEncode(inFile, pspEncoderMode, pspEncoderQuality, anamorphMode, videoPar, audioTrack, encAudio, subsTrack)

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
            configEncoder(inputPath)
        else:
            print(f':: Input File is Not Allowed File Type: {inputPath}')
    elif os.path.isdir(inputPath):
        print(f':: Input Folder: {inputPath}')
        configEncoder(inputPath)
    else:
        print(f':: Input Path is Not a Folder or Video File: {inputPath}')
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
