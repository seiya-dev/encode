#!/usr/bin/env python3

# set libs
import sys
import os
import re

from pathlib import Path
from pathlib import PurePath

import time
import subprocess
import json

def extractFile(file: Path):
    # get mkv data
    result = subprocess.run([
        'mkvmerge',
        '-J',
        file,
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # parse mkv results
    result = json.loads(result.stdout.decode('utf-8'))
    mkvfile = PurePath(result['file_name']).stem
    outdir  = PurePath(result['file_name']).parent
    # print filename
    print(f'\n:: FILE: {mkvfile}.mkv')
    # set ids
    countTr = { 'video': 0, 'audio': 0, 'subtitles': 0 }
    namesTr = []
    trackTp = {}
    trackNm = {}
    # list tracks
    if 'tracks' in result:
        for t in result['tracks']:
            p = t['properties']
            track_tid = f'{t["type"][:1]}:{countTr[t["type"]]}'
            track_name = '/ ' + p['track_name'] if 'track_name' in p else ''
            language = p['language_ietf'] if 'language_ietf' in p else p['language']
            printData = ' '.join([
                f'#{t["id"]}',
                track_tid,
                f'{t["type"].capitalize()}:',
                t["codec"],
                f'/ {language}',
                track_name,
            ])
            namesTr.append(printData)
            trackTp[track_tid] = t['id']
            if 'track_name' in p:
                trackNm[p['track_name']] = t['id']
            print(printData)
            countTr[t['type']] = countTr[t['type']] + 1
    if 'attachments' in result:
        for a in result['attachments']:
            print(f'Attachment #{a["id"]}: {a["content_type"]} {a["file_name"]}')
    # select track
    global isFile
    global trackIndex
    if trackIndex is None or isFile == True:
        trackIndex = input('\n:: Track Index or Track Name to Extract: ')
    # check
    trackIndexNum = -1
    if trackIndex in trackTp:
        trackIndexNum = trackTp[trackIndex]
    if trackIndex in trackNm:
        trackIndexNum = trackNm[trackIndex]
    try:
        if trackIndexNum > -1:
            trackIndexNum = int(trackIndexNum)
        else:
            trackIndexNum = int(trackIndex)
        if -1 > trackIndexNum > len(result['tracks']):
            trackIndexNum = -1
    except ValueError:
        trackIndexNum = -1
    # selected
    print(f'Selected: {trackIndexNum}')
    # extract
    if trackIndexNum > -1:
        # select track extension
        trackCodec = result['tracks'][trackIndexNum]['properties']['codec_id']
        trackExt = 'bin'
        if trackCodec == 'V_MPEG4/ISO/AVC':
            trackExt = '264'
        if trackCodec == 'V_MPEG4/ISO/HEVC':
            trackExt = '265'
        if trackCodec == 'V_MPEGH/ISO/HEVC':
            trackExt = '265'
        if trackCodec == 'V_THEORA':
            trackExt = 'ogv'
        if trackCodec == 'A_AAC':
            trackExt = 'aac'
        if trackCodec == 'A_AC3':
            trackExt = 'ac3'
        if trackCodec == 'A_FLAC':
            trackExt = 'flac'
        if trackCodec == 'A_VORBIS':
            trackExt = 'ogg'
        if trackCodec == 'S_TEXT/ASS':
            trackExt = 'ass'
        if trackCodec == 'S_TEXT/UTF8':
            trackExt = 'srt'
        # do extract
        output = os.path.join(outdir, f'{PurePath(file).stem}_track{trackIndexNum+1}.{trackExt}')
        subprocess.call(['mkvextract', '--ui-language', 'en', 'tracks', file, f'{trackIndexNum}:{output}'])
    if isFile == True:
        extractFile(file)

def extractFolder(inputPath: Path):
    print(f'\n:: Selected path: {os.path.abspath(inputPath)}')
    for file in os.listdir(inputPath):
        file = os.path.join(inputPath, file)
        if file.lower().endswith('.mkv'):
            extractFile(file)

# set default
isFile = False
trackIndex = None

# set folder
if len(sys.argv) < 2:
    inputPath = input(':: Folder/File: ')
else:
    inputPath = sys.argv[1]

# check path
if not os.path.isdir(inputPath):
    if os.path.isfile(inputPath) and PurePath(inputPath).suffix.lower() == '.mkv':
        isFile = True
        extractFile(inputPath)
    else:
        print(f':: Path is not a mkv file or folder: "{inputPath}"!')
else:
    extractFolder(inputPath)

# end
if os.environ.get('isBatch') is None:
    input('\n:: Press any key to continue...\n')
