#!/usr/bin/env python3

# set libs
import os
import subprocess
import sys
from pathlib import Path

try:
    import questionary
except ModuleNotFoundError:
    print(':: Please install "questionary" module: pip install questionary')
    input(':: Press enter to continue...\n')
    exit()

from _encHelper import PathValidator


def extractFolder(inputPath: Path):
    absPath = str(os.path.abspath(inputPath)).replace('\\', '/')
    print(f'\n:: Selected path: {absPath}')
    attExtCmd = ['SubtitleEdit', '/convert', f'{absPath}/*.srt', 'AdvancedSubStationAlpha']
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
        print(f':: Path is not a folder: "{inputPath}"!')
    else:
        extractFolder(inputPath)
except Exception as err:
    print(':: Something goes wrong...')
    print(f':: {type(err).__name__}: {err}')
    print(err)

# end
if os.environ.get('ISBATCH') is None:
    questionary.press_any_key_to_continue(message = '\n:: Press enter to continue...\n').ask()
