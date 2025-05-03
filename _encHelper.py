import io
import os
import re
import json
import zlib
import struct
import argparse
import subprocess

from typing import List
from pathlib import Path
from pathlib import PurePath

def moduleNotFound(text: str) -> str:
    fmodule = re.search(r'\'(.*)\'', text)
    returnText = ':: Please install required module'
    if fmodule:
        fmodule = fmodule.group().strip('\'')
        if fmodule == 'numpy':
            returnText = f'{returnText}: pip install numpy'
        if fmodule == 'PIL':
            returnText = f'{returnText}: pip install pillow'
        if fmodule == 'questionary':
            returnText = f'{returnText}: pip install questionary'
    print(returnText)
    input(':: Press enter to continue...\n')

try:
    from questionary import Choice, Validator, ValidationError
    from PIL import Image
    import numpy as np
except ModuleNotFoundError as errorModule:
    moduleNotFound(str(errorModule))
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

# crc32 calc
def calculate_crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xffffffff

# create empty image
def create_img(width, height):
    return Image.new('RGBA', (width, height), (0, 0, 0, 0))

# trim image
def trim_img(img, threshold=19):
    # Get the alpha channel (transparency)
    alpha = img.getchannel('A')
    alpha_np = np.array(alpha)
    
    # Create a mask where alpha is above the threshold
    mask = alpha_np > int(threshold / 100 * 255)
    if not np.any(mask):
        return img, (0, 0)

    # Get the bounding box of the non-transparent region
    coords = np.argwhere(mask)
    y0, x0 = coords.min(axis=0)
    y1, x1 = coords.max(axis=0) + 1  # slices are exclusive
    trimmed_img = img.crop((x0, y0, x1, y1))
    return trimmed_img, (x0, y0)

# png header
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
class NotPNGError(Exception): pass
class NotAPNGError(Exception): pass
def is_not_png(err): return isinstance(err, NotPNGError)
def is_not_apng(err): return isinstance(err, NotAPNGError)

# iphone png to standart png
def strip_cgbi_and_fix_png(buffer: bytes, remove_alpha_premult: bool = True) -> bytes:
    if buffer[:8] != PNG_SIGNATURE:
        raise NotPNGError('Not a PNG')
    
    # check CgBI chunk
    offset = 8
    chunks = []
    is_cgbi_png = False
    while offset < len(buffer):
        length = struct.unpack('>I', buffer[offset:offset + 4])[0]
        chunk_type = buffer[offset + 4:offset + 8]
        if chunk_type != b'CgBI':
            chunks.append(buffer[offset:offset + 12 + length])
        else:
            is_cgbi_png = True
        offset += 12 + length
        if chunk_type == b'IEND':
            break
    
    # not iphone png
    if not is_cgbi_png:
        return buffer
    
    # Rebuild PNG without CgBI
    rebuilt_png = PNG_SIGNATURE + b''.join(chunks)
    
    # Load image from memory buffer
    with io.BytesIO(rebuilt_png) as img_buffer:
        img = Image.open(img_buffer)
        img = img.convert('RGBA')
    
    # Process pixels
    arr = np.array(img)
    arr = arr[..., [2, 1, 0, 3]]  # Swap BGR -> RGB
    if remove_alpha_premult:
        alpha = arr[..., 3:4]
        nonzero_alpha = alpha != 0
        
        rgb = arr[..., :3]
        adjusted_rgb = (
            (rgb[nonzero_alpha] * 255 + alpha[nonzero_alpha] // 2) // alpha[nonzero_alpha]
        )
        arr[..., :3][nonzero_alpha] = np.clip(adjusted_rgb, 0, 255)

    # Save image back to Image
    output_buffer = io.BytesIO()
    final_img = Image.fromarray(arr.astype('uint8'), 'RGBA')
    final_img.save(output_buffer, format='PNG')
    return final_img

# apng structure
class APNG:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.num_plays = 0
        self.play_time = 0
        self.frames: List[Frame] = []
class APNGFrame:
    def __init__(self):
        self.left = 0
        self.top = 0
        self.width = 0
        self.height = 0
        self.delay_num = 0
        self.delay_den = 100
        self.delay_ms = 0
        self.disposeOp = 0
        self.blendOp = 0
        self.data = None

# apng parser
def parse_apng(buffer: bytes) -> APNG:
    if buffer[:8] != PNG_SIGNATURE:
        raise NotPNGError('Not a PNG')
    
    offset = 8
    is_animated = False
    while offset < len(buffer):
        length = struct.unpack('>I', buffer[offset:offset + 4])[0]
        chunk_type = buffer[offset + 4:offset + 8].decode('ascii')
        if chunk_type == 'acTL':
            is_animated = True
            break
        offset += 12 + length
        if chunk_type == 'IEND':
            break
    
    if not is_animated:
        raise NotAPNGError('Not an animated PNG')
    
    apng = APNG()
    
    pre_data_parts, post_data_parts = [], []
    header_data_bytes = None
    
    frame = None
    frame_number = 0
    offset = 8
    
    while offset < len(buffer):
        length = struct.unpack('>I', buffer[offset:offset + 4])[0]
        chunk_type = buffer[offset + 4:offset + 8].decode('ascii')
        chunk_data = buffer[offset + 8: offset + 8 + length]
        
        if chunk_type == 'IHDR':
            header_data_bytes = chunk_data
            apng.width, apng.height = struct.unpack('>II', chunk_data[:8])
        
        elif chunk_type == 'acTL':
            apng.num_plays = struct.unpack('>I', chunk_data[4:8])[0]
        
        elif chunk_type == 'fcTL':
            if frame:
                apng.frames.append(frame)
                frame_number += 1
            
            frame = APNGFrame()
            frame.width, frame.height = struct.unpack('>II', chunk_data[4:12])
            frame.left, frame.top = struct.unpack('>II', chunk_data[12:20])
            frame.delay_num, frame.delay_den = struct.unpack('>HH', chunk_data[20:24])
            if frame.delay_den == 0:
                print(f':: FRAME #{frame_number+1} DENOMINATOR DELAY WAS FIXED!')
                frame.delay_den = 100
            
            frame.delay_ms = (frame.delay_num / frame.delay_den) * 1000
            apng.play_time += frame.delay_ms
            
            frame.disposeOp, frame.blendOp = chunk_data[24], chunk_data[25]
            if frame_number == 0 and frame.disposeOp == 2:
                frame.disposeOp = 1

        elif chunk_type in ('IDAT', 'fdAT'):
            if frame:
                data_start = 12 if chunk_type == 'fdAT' else 8
                if not hasattr(frame, 'data_parts'):
                    frame.data_parts = []
                frame.data_parts.append(buffer[offset + data_start: offset + 8 + length])
        
        elif chunk_type == 'IEND':
            post_data_parts.append(buffer[offset: offset + 12 + length])
        
        else:
            pre_data_parts.append(buffer[offset: offset + 12 + length])
        
        offset += 12 + length
        if chunk_type == 'IEND':
            break
    
    if frame:
        apng.frames.append(frame)
    
    if not apng.frames:
        raise NotAPNGError('No animation frames found')
    
    apng.play_time = round(apng.play_time, 3)
    pre_blob = b''.join(pre_data_parts)
    post_blob = b''.join(post_data_parts)
    
    for frame in apng.frames:
        bb = bytearray(PNG_SIGNATURE)
        header_copy = bytearray(header_data_bytes)
        header_copy[0:4] = frame.width.to_bytes(4, 'big')
        header_copy[4:8] = frame.height.to_bytes(4, 'big')
        bb.extend(make_chunk_bytes('IHDR', header_copy))
        bb.extend(pre_blob)
        for part in getattr(frame, 'data_parts', []):
            bb.extend(make_chunk_bytes('IDAT', part))
        bb.extend(post_blob)
        frame.image_data = io.BytesIO(bb)
        del frame.data_parts  # cleanup
    
    current_frame = create_img(apng.width, apng.height)
    
    for frame in apng.frames:
        image_data = Image.open(frame.image_data).convert('RGBA')
        previous_frame = current_frame.copy()
        del frame.image_data
        
        if frame.blendOp == 1:
            current_frame.paste(image_data, (frame.left, frame.top), image_data)
        else:
            cur_data = np.array(current_frame)
            overlay = np.array(image_data)
            
            y1, y2 = frame.top, frame.top + frame.height
            x1, x2 = frame.left, frame.left + frame.width
            
            cur_data[y1:y2, x1:x2] = overlay
            current_frame = Image.fromarray(cur_data, 'RGBA')
         
        frame.data = current_frame
        
        if frame.disposeOp == 1:
            current_frame = create_img(apng.width, apng.height)
        elif frame.disposeOp == 2:
            current_frame = previous_frame
    
    return apng

# make png chunk
def make_chunk_bytes(chunk_type: str, data_bytes: bytes) -> bytes:
    chunk_type_bytes = chunk_type.encode('ascii')
    crc = calculate_crc32(chunk_type_bytes + data_bytes)
    return (
        struct.pack('>I', len(data_bytes)) +
        chunk_type_bytes +
        data_bytes +
        struct.pack('>I', crc)
    )
