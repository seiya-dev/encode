#!/usr/bin/env python3

import os
import subprocess
import sys
import time
from pathlib import Path, PurePath

try:
    from _encHelper import (
        IntValidator,
        PathValidator,
        audioTitle,
        extVideoFile,
        fixPath,
        getMediaData,
        moduleNotFound,
        searchSubsFile,
    )
except ModuleNotFoundError:
    print(':: EncHelper Not Found...')
    input(':: Press enter to continue...\n')
    exit()

try:
    from questionary import Choice
    from questionary import confirm as qconfirm
    from questionary import press_any_key_to_continue as qpause
    from questionary import select as qselect
    from questionary import text as qtext
except ModuleNotFoundError as errorModule:
    moduleNotFound(str(errorModule))
    exit()


# file
def configFile(inFile: Path):
    outFolder = PurePath(inFile).parent
    outFile = f'{outFolder}/{PurePath(inFile).stem} [enc].mp4'
    inFonts = fixPath(f'{outFolder}/fonts', True)

    videoData = getMediaData(inFile, 'v', True)
    if len(videoData) < 1:
        print()
        print(f':: Skipping: {PurePath(inFile).name}')
        print(':: No video streams!')
        return

    videoInfo = getMediaData(inFile)
    videoDur = round(float(videoInfo['format']['duration']))
    videoDur_h, videoDur_r = divmod(videoDur, 3600)
    videoDur_m, videoDur_s = divmod(videoDur_r, 60)
    print(f':: Duration : {videoDur_h:02.0f}:{videoDur_m:02.0f}:{videoDur_s:02.0f}')

    vFilters = '[0:v:0]format=yuv420p'
    encCrf = qtext('Set Encode CRF:', validate=IntValidator, default='20').ask()

    audioList = []
    audioData = getMediaData(inFile, 'a')
    for t in range(len(audioData)):
        tname = audioTitle(audioData, t)
        audioList.append(Choice(f'[{str(t).rjust(2)}]: {tname}', value=t))
    audioList.append(Choice('[-1]: No Audio', value='-1'))

    audioCmd = []
    audioTrack = qselect('Select Audio Track:', audioList).ask()
    if audioTrack != '-1':
        encodeAudio = qconfirm(
            'Encode Audio to AAC 192k 2ch (Default=No):', default=False
        ).ask()
        atid = int(audioTrack)
        if encodeAudio:
            audioCmd = [
                '-map',
                f'0:a:{atid}?',
                '-c:a',
                'aac',
                '-cutoff',
                '0',
                '-b:a',
                '192k',
                '-ac',
                '2',
            ]
        else:
            audioCmd = ['-map', f'0:a:{atid}?', '-c:a', 'copy']

    vTitle = qtext('Set Video Title:').ask()

    subsData = searchSubsFile(inFile)
    subsTrack = qselect('Subtitle For HardSubs:', subsData.sel).ask()
    if subsTrack != '-1':
        inSubs = subsData.inf[subsTrack]
        inSubsFile = fixPath(inSubs['file'], True)
        tid = int(subsTrack.split(':')[1])

        outsubs = f"filename='{inSubsFile}'"
        overlay = False

        if inSubs['ext']:
            outsubs = f"subtitles={outsubs}:fontsdir='{inFonts}'"
        else:
            subsCodec = inSubs['codec']
            if subsCodec == 'dvd_subtitle' or subsCodec == 'hdmv_pgs_subtitle':
                overlay = True
                outsubs = f'[v];[v][0:s:{tid}]overlay'
            else:
                outsubs = f"subtitles={outsubs}:stream_index={tid}:fontsdir='{inFonts}'"
        comaadd = ',' if not overlay else ''
        vFilters = f'{vFilters}{comaadd}{outsubs}'

    encCmd = []
    encCmd.extend(
        [
            r'ffmpeg',
            '-hide_banner',
        ]
    )
    encCmd.extend(
        [
            '-loglevel',
            'error',
            '-stats',
        ]
    )
    encCmd.extend(
        [
            '-hwaccel',
            'auto',
        ]
    )
    encCmd.extend(['-fflags', '+bitexact'])
    encCmd.extend(['-flags:v', '+bitexact'])
    encCmd.extend(['-flags:a', '+bitexact'])

    encCmd.extend(['-i', inFile])
    if audioTrack == '-1':
        encCmd.extend(['-an'])
    encCmd.extend(['-sn', '-dn'])

    encCmd.extend(['-filter_complex', f'{vFilters}[video]'])

    encCmd.extend(['-map', '[video]', '-c:v', 'libx264', '-crf', encCrf])
    encCmd.extend(['-preset:v', 'faster', '-tune:v', 'animation'])
    if len(audioCmd) > 0:
        encCmd.extend(audioCmd)

    encCmd.extend(['-map_metadata', '-1', '-map_chapters', '-1'])
    encCmd.extend(['-metadata', 'application='])
    encCmd.extend(['-metadata', 'writing_library='])
    if vTitle != '':
        encCmd.extend(['-metadata:s:v:0', f'title={vTitle}'])

    # encCmd.extend([ '-brand', 'mp42' ])
    encCmd.extend([outFile])

    startTime = time.monotonic()
    subprocess.run(encCmd)

    runTime = time.monotonic() - startTime
    hours, rem = divmod(runTime, 3600)
    minutes, seconds = divmod(rem, 60)
    print(
        f'\n:: Encoded {PurePath(outFile).name} in {hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}'
    )


# folder
def configFolder(inPath: Path):
    print(f'\n:: Selected path: {os.path.abspath(inPath)}')
    print('script not usable for dir!')


# set folder
if len(sys.argv) < 2:
    inputPath = qtext(':: Folder/File: ', validate=PathValidator).ask()
    inputPath = inputPath.strip('"')
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
    print(':: Something goes wrong...')
    print(f':: {type(err).__name__}: {err}')

# end
if os.environ.get('ISBATCH') is None:
    qpause(message='\n:: Press enter to continue...\n').ask()
