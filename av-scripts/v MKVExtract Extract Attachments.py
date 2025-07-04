#!/usr/bin/env python3

# set libs
import os
import re
import sys
import json
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
from _encHelper import getMediaData, getMKVData, audioTitle, searchSubsFile

def extractFile(file: Path):
    # get mkv data
    result = getMKVData(file)
    # parse mkv results
    mkvfile = PurePath(result['file_name']).stem
    outdir  = os.path.join(PurePath(result['file_name']).parent, 'fonts')
    attExtCmd = ['mkvextract', '--ui-language', 'en', 'attachments', file]
    # print filename
    print(f'\n:: FILE: {mkvfile}.mkv')
    # parse tracks
    countTr = { 'video': 0, 'audio': 0, 'subtitles': 0 }
    if 'tracks' in result:
        for t in result['tracks']:
            p = t['properties']
            track_name = '/ ' + p['track_name'] if 'track_name' in p else ''
            language = p['language_ietf'] if 'language_ietf' in p else p['language']
            printData = ' '.join([
                f'#{t["id"]}',
                t["type"].capitalize(),
                f'#{countTr[t["type"]]}:',
                p["codec_id"],
                f'({t["codec"]})',
                f'/ {language}',
                track_name,
            ])
            print(printData)
            countTr[t['type']] = countTr[t['type']] + 1
    if 'attachments' in result:
        for a in result['attachments']:
            print(f'Attachment #{a["id"]}: {a["content_type"]} {a["file_name"]}')
            fntPath = os.path.join(outdir, a['file_name'])
            attExtCmd.append(f'{a["id"]}:{fntPath}')
    if 'attachments' in result and len(result['attachments']) > 0:
        if os.path.isfile(outdir):
            os.remove(outdir)
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        subprocess.run(attExtCmd)
    
    attExtCmd = ['mkvextract', file, 'chapters', '--ui-language', 'en', '-s', f'{file}.chapters.txt']
    subprocess.run(attExtCmd)

def extractFolder(inputPath: Path):
    print(f'\n:: Selected path: {os.path.abspath(inputPath)}')
    for file in os.listdir(inputPath):
        file = os.path.join(inputPath, file)
        if file.lower().endswith('.mkv'):
            extractFile(file)

# set folder
if len(sys.argv) < 2:
    inputPath = questionary.text(':: Folder/File: ', validate=PathValidator).ask()
    inputPath = inputPath.strip('\"')
else:
    inputPath = sys.argv[1]

# check path
try:
    if not os.path.isdir(inputPath):
        if os.path.isfile(inputPath) and PurePath(inputPath).suffix.lower() == '.mkv':
            extractFile(inputPath)
        else:
            print(f':: Path is not a mkv file or folder: "{inputPath}"!')
    else:
        extractFolder(inputPath)
except Exception as err:
    print(f':: Something goes wrong...')
    print(f':: {type(err).__name__}: {err}')
    print(err)

# end
if os.environ.get('isBatch') is None:
    questionary.press_any_key_to_continue(message = '\n:: Press enter to continue...\n').ask()
