#!/usr/bin/env python3

import sys
import os
import re

from pathlib import Path
from pathlib import PurePath

import time
import subprocess

try:
    import questionary
    from questionary import Choice, Validator, ValidationError
except ModuleNotFoundError:
    print(':: Please install "questionary" module: pip install questionary')
    input(':: Press enter to continue...\n')
    exit()

from _encHelper import boolYN, IntValidator, PathValidator, extVideoFile, fixPath
from _encHelper import getMediaData, audioTitle, searchSubsFile

def renameFile(inFile: Path, targetTitle: str):
    
    outFolder = PurePath(inFile).parent
    outName   = PurePath(inFile).stem
    
    if m := re.search(reSETartget, outName):
        episode, ext = m.group('episode'), m.group('ext')
        if targetTitle == '':
            print(f':: Wrong input: Please set title!')
            return
    elif m := re.match(reTarget, outName):
        title, episode, ext = m.group('title'), m.group('episode'), m.group('ext')
        if re.search(' -$', title):
            title = re.sub(' -$', '', title)
        if targetTitle == '':
            targetTitle = title
    else:
        return
    
    formFile = f'{outFolder}/{outName}.mp4'
    ext = ext if ext == 'orig' else f'{ext}p'
    toFile = f'{outFolder}/{targetTitle} - {episode} [{ext}].mp4'
    os.rename(formFile, toFile)

def checkFolder(inputPath: Path):
    print(f':: Selected path: {inputPath}\n')
    
    targetTitle = input(':: Target title: ')
    
    if os.path.isdir(inputPath):
        for file in os.listdir(inputPath):
            file = os.path.join(inputPath, file)
            if file.lower().endswith('.mp4'):
                renameFile(file, targetTitle)

# set folder
if len(sys.argv) < 2:
    inputPath = questionary.text(':: Folder: ', validate=PathValidator).ask()
    inputPath = inputPath.strip('\"')
else:
    inputPath = sys.argv[1]

# input to path
reSETartget = r'S\d+E(?P<episode>\d+?)(-|\.).+-(?P<ext>(720|1080|orig)?)-enc'
reTarget = r'(\[[^\[\]]*?\]|\([^\(\)]*?\)) (?P<title>.+( \d)?)( -)? (Ep)?(?P<episode>((SP)?\d+|OVA( )?(\d+)?)(v\d)?) .+-(?P<ext>(720|1080|orig)?)-enc'

# check path
if not os.path.isdir(inputPath):
    print(f':: Path is not a folder: "{inputPath}"!')
else:
    checkFolder(inputPath)

# end
if os.environ.get('isBatch') is None:
    questionary.press_any_key_to_continue(message = '\n:: Press enter to continue...\n').ask()
