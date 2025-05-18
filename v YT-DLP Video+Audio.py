#!/usr/bin/env python3

import os
import re
import sys
import subprocess

try:
    from questionary press_any_key_to_continue as qpause
    from questionary import text as qtext, select as qselect, confirm as qconfirm
    from questionary import Choice, Validator, ValidationError
except ModuleNotFoundError:
    print(':: Please install "questionary" module: pip install questionary')
    input(':: Press enter to continue...\n')
    exit()

# file
def configInput():
    input_url = questionary.text(':: Input URL:').ask()
    
    ytCmd = list()
    cookiePath = os.path.expanduser('~/.config/yt-dlp-cookies.txt')
    ytCmd.extend([ r'yt-dlp', '--cookies', cookiePath ])
    
    checkUrl = ytCmd.copy()
    checkUrl.extend(['-F', input_url])
    
    ytdata = subprocess.run(checkUrl)
    
    if ytdata.returncode != 0:
        print()
        configInput()
        return
    
    print(f'\n:: Format Exampe: bv*[height>=720][ext=mp4][vcodec^=avc1][protocol*=m3u8]+ba*[ext=m4a]')
    print(f':: Format Exampe: bestvideo[ext=mp4],bestaudio[ext=m4a]/best[ext=mp4]/best')
    vformat = qtext(':: Video/Audio Format:').ask()
    ytCmd.extend(['--format', vformat])
    
    mformatList = [ 'mkv', 'mp4', 'webm', 'mov', 'flv', 'avi' ]
    mformat = qselect(':: Merge Format:', choices=mformatList).ask()
    ytCmd.extend(['--merge-output-format', mformat])
    
    if mformat == 'mkv':
        dlAllSubs = qconfirm(':: Download All Subtitles (Default=No):', default=False).ask()
        if dlAllSubs:
            ytCmd.extend(['--all-subs'])
    
    keepSource = qconfirm(':: Keep Source Data (Default=No):', default=False).ask()
    if keepSource:
        ytCmd.extend(['--keep-video'])
    
    vOutFp = qtext(':: Output Path:', default=os.getcwd()).ask()
    vOutFnDef = f'%(title)s [%(id)s %(height)s f%(format_id)s].{mformat}'
    vOutFn = qtext(':: Output Filename:', default=vOutFnDef).ask()
    
    ytCmd.extend(['-o', vOutFn])
    ytCmd.extend(['--concurrent-fragments', '10', input_url ])
    
    try:
        os.chdir(vOutFp)
    except Exception as err:
        print(':: Error: Failed to change folder!')
        print(f':: {type(err).__name__}: {err}')
    
    print(f'\n:: RUN: {ytCmd}')
    subprocess.run(ytCmd)

try:
    configInput()
except FileNotFoundError:
    print(':: ERROR: YT-DLP Not Installed!')
except Exception as err:
    print(f':: Something goes wrong...')
    print(f':: {type(err).__name__}: {err}')

# end
if os.environ.get('isBatch') is None:
    qpause(message = '\n:: Press enter to continue...\n').ask()
