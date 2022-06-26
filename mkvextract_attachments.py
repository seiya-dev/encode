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
    if 'attachments' in result:
        if os.path.isfile(outdir):
            os.remove(outdir)
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        subprocess.call(attExtCmd)

def extractFolder(inputPath: Path):
    print(f'\n:: Selected path: {os.path.abspath(inputPath)}')
    for file in os.listdir(inputPath):
        file = os.path.join(inputPath, file)
        if file.lower().endswith('.mkv'):
            extractFile(file)

# set folder
if len(sys.argv) < 2:
    inputPath = input(':: Folder/File: ')
else:
    inputPath = sys.argv[1]

# check path
if not os.path.isdir(inputPath):
    if os.path.isfile(inputPath) and PurePath(inputPath).suffix.lower() == '.mkv':
        extractFile(inputPath)
    else:
        print(f':: Path is not a mkv file or folder: "{inputPath}"!')
else:
    extractFolder(inputPath)

# end
if os.environ.get('isBatch') is None:
    input('\n:: Press any key to continue...\n')
