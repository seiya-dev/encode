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

def extractFolder(inputPath: Path):
    absPath = str(os.path.abspath(inputPath)).replace('\\', '/')
    print(f'\n:: Selected path: {absPath}')
    attExtCmd = ['SubtitleEdit', '/convert', f'{absPath}/*.srt', 'webvtt']
    subprocess.run(attExtCmd)

# set folder
if len(sys.argv) < 2:
    inputPath = questionary.text(':: Folder/File: ', validate=PathValidator).ask()
    inputPath = inputPath.strip('\"')
else:
    inputPath = sys.argv[1]

# check path
try:
    if not os.path.isdir(inputPath):
        if os.path.isfile(inputPath):
            extractFile(inputPath)
        else:
            print(f':: Path is not a folder: "{inputPath}"!')
    else:
        extractFolder(inputPath)
except Exception as err:
    print(f':: Something goes wrong...')
    print(f':: {type(err).__name__}: {err}')
    print(err)

# end
if os.environ.get('isBatch') is None:
    questionary.press_any_key_to_continue(message = '\n:: Press enter to continue...\n').ask()
