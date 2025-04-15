import os
import re
import json
import argparse
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

# int validator
def IntValidator(text: str) -> bool:
    if len(text) == 0:
        return False
    try:
        int(text)
    except ValueError:
        return False
    return True

# float validator
def FloatValidatorP(text: str) -> bool:
    try:
        boolF = float(text) > 0
    except ValueError:
        return False
    return boolF

# check path
def PathValidator(text: str) -> bool:
    text = text.strip('\"')
    if len(text) == 0:
        return False
    return os.path.exists(text)

# check y/n
def boolYN(text: str) -> bool:
    text = str(text).lower().strip()
    if len(text) > 0 and text[0] == 'y':
        return True
    else:
        return False

# fix paths
def fixPath(inFile: Path, forFFmpeg: bool = False):
    inFile = inFile.replace('\\', '/')
    if forFFmpeg:
        inFile = inFile.replace(':', r'\:')
        if os.name == 'nt':
            inFile = inFile.replace("'", r"'\\\''")
        else:
            inFile = inFile.replace("'", r"'\''")
    return inFile

# acceptable extensions
extVideoFile = ['.mkv', '.mp4', '.mov', '.avi', '.avs']
extAudioFile = ['.mka', '.m4a', '.aac', '.flac', '.eac3', '.mp3', '.wav']
extSubsFile  = ['.ass', '.srt']

# search files
def searchMedia(inputPath: Path, prefixName: str, extFilter: list) -> list:
    inputPath = str(inputPath)
    
    fsList = list()
    baseLevel = len(inputPath.split(os.path.sep))
    
    for root, dirs, files in os.walk(inputPath):
        curLevel = len(root.split(os.path.sep))
        if curLevel < baseLevel + 3:
            for file in files:
                fileExt = PurePath(file).suffix.lower()
                if file.startswith(prefixName) and extFilter.count(fileExt) > 0:
                    inFile = argparse.Namespace()
                    inFile.path = os.path.join(os.path.sep, root, file)
                    inFile.name = inFile.path.replace(f'{inputPath}{os.path.sep}', '')
                    inFile.ext = fileExt[1:]
                    fsList.append(inFile)
    
    return fsList

# get mkv info
def getMKVData(inputPath: Path) -> dict:
    mkvcmd = [ 'mkvmerge', '-J', inputPath ]
    result = subprocess.run(mkvcmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = json.loads(result.stdout.decode('utf-8'))
    return result

# get media info
def getMediaInfo(inputPath: Path) -> dict:
    micmd = [ 'MediaInfo', '--Output=JSON', inputPath ]
    result = subprocess.run(micmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = json.loads(result.stdout.decode('utf-8'))
    return result

# get data from video file
def getMediaData(inputPath: Path, streamType: str = '', showLog: bool = False) -> dict:
    ffProbeCmd = list()
    ffProbeCmd.extend([ r'ffprobe', '-v', 'error', '-hide_banner', ])
    ffProbeCmd.extend([ '-print_format', 'json', '-show_format', '-show_streams', ])
    if streamType != '':
        ffProbeCmd.extend([ '-select_streams', streamType, ])
    ffProbeCmd.extend([ inputPath ])
    
    result = subprocess.run(ffProbeCmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = result.stdout
    
    try:
        result = result.decode('utf-8')
    except:
        result = result.decode('ISO-8859-1')
    
    lwiCreate = re.search(r'^Creating lwi index file .*', result, flags=re.M)
    if lwiCreate:
        print(f'[:info:] LWI Index file created!')
    if showLog:
        libassLog = re.findall(r'^libass: .*', result, flags=re.M)
        if libassLog:
            print()
            for i in range(len(libassLog)):
                print(f'[:info:] {libassLog[i]}')
        avisynthLog = re.findall(r'^\[avisynth .*', result, flags=re.M)
        if avisynthLog:
            print()
            for i in range(len(avisynthLog)):
                print(f'[:info:] {avisynthLog[i]}')
    result = re.sub(r'^Creating lwi index file .*', '', result, flags=re.M)
    result = re.sub(r'^libass: .*', '', result, flags=re.M)
    result = re.sub(r'^\[avisynth .*', '', result, flags=re.M)
    result = re.sub(r'^\w.*', '', result, flags=re.M)
    result = re.sub(r'^\(.*', '', result, flags=re.M)
    
    try:
        result = json.loads(result)
    except:
        print(':: FAILED TO GET MEDIA DATA')
    
    result = result if 'streams' in result else {'streams':list()}
    result = result if streamType == '' else result['streams']
    return result

def audioTitle(audioData: dict, trackId: int, returnCodec: bool = False) -> str:
    a = audioData[trackId]
    
    if not 'codec_name' in a and 'codec_tag_string' in a:
        a['codec_name'] = a['codec_tag_string']
    
    t        = a['tags']       if 'tags'       in a else dict()
    codec    = a['codec_name'] if 'codec_name' in a else 'UNK_CODEC'
    channels = a['channels']   if 'channels'   in a else '?'
    lang     = t['language']   if 'language'   in t else 'UNK'
    title    = t['title']      if 'title'      in t else 'NO_TITLE'
    
    tname = f'{codec} {channels}ch {lang} {title}'.strip()
    
    if returnCodec:
        return tname, codec
    else:
        return tname

def subsTitle(subsData: dict, trackId: int, returnCodec: bool = False) -> str:
    s = subsData[trackId]
    
    if not 'codec_name' in s and 'codec_tag_string' in s:
        s['codec_name'] = s['codec_tag_string']
    
    t      = s['tags']       if 'tags'       in s else dict()
    codec  = s['codec_name'] if 'codec_name' in s else 'UNK_CODEC'
    lang   = t['language']   if 'language'   in t else 'UNK'
    title  = t['title']      if 'title'      in t else 'NO_TITLE'
    
    tname = f'{lang} {title} #{codec}'.strip()
    
    if 'NUMBER_OF_BYTES' in t and (codec == 'dvd_subtitle' or codec == 'hdmv_pgs_subtitle'):
        bInt = t['NUMBER_OF_BYTES']
        tname += f' ({bInt} bytes)'
    
    if returnCodec:
        return tname, codec
    else:
        return tname

# find subs files
def searchSubsFile(inputPath: Path, searchExtSubsFile: list = extSubsFile):
    subsData = argparse.Namespace()
    subsData.root = str(PurePath(inputPath).parent)
    subsData.prefix = str(PurePath(inputPath).stem)
    inFileExt = str(PurePath(inputPath).suffix.lower())
    
    fileIdx = -1
    subsData.sel = list()
    subsData.inf = dict()
    
    if inFileExt == '.mkv':
        subsDataMKV = getMediaData(inputPath, 's')
        if len(subsDataMKV) > 0:
            fileIdx += 1
            for t in range(len(subsDataMKV)):
                
                track_id   = f'{fileIdx}:{t}'
                track_name, codec = subsTitle(subsDataMKV, t, True)
                
                subsData.inf[track_id] = { "file": inputPath, "codec": codec, "title": track_name, "ext": False }
                subsData.sel.append(Choice(f'[{track_id}]: [MKV] {track_name}', value=track_id))
    
    extSubs = searchMedia(subsData.root, subsData.prefix, searchExtSubsFile)
    for s in extSubs:
        fileIdx += 1
        track_id = f'{fileIdx}:0'
        
        subsData.inf[track_id] = { "file": s.path, "codec": s.ext, "title": s.name, "ext": True }
        subsData.sel.append(Choice(f'[{track_id}]: {s.name}', value=track_id))
    
    subsData.inf['-1'] = { "file": None, "codec": None, "title": None, "ext": True }
    subsData.sel.append(Choice('[ -1]: Skip', value='-1'))
    return subsData
