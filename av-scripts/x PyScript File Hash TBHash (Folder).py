import os
import sys
import json
import zlib
import hashlib
from pathlib import Path

try:
    from _encHelper import moduleNotFound
    from _encHelper import PathValidator
except ModuleNotFoundError as errorModule:
    print(':: EncHelper Not Found...')
    input(':: Press enter to continue...\n')
    exit()

try:
    from questionary import text as qtext
    from questionary import press_any_key_to_continue as qpause
    from tqdm import tqdm
    import yaml
except ModuleNotFoundError as errorModule:
    moduleNotFound(str(errorModule))
    exit()

ALLOWED_EXT = ('.mkv', '.mp4', '.avi', '.mka', '.flac', '.wav', '.7z')
BLOCK_SIZE = 1024 * 256 # 256 KiB

def get_chunk_size(file_size):
    LIMIT_SIZES = [4, 8, 16, 32, 64, 128]
    MiB = 1024 * 1024
    GiB = 1024 * MiB
    
    for limit in LIMIT_SIZES:
        if file_size <= limit * GiB:
            return limit * MiB
    return LIMIT_SIZES[-1] * MiB

def hash_file(file_path, file_size):
    chunk_size = get_chunk_size(file_size)
    
    crc = 0
    md5file = hashlib.md5()
    md5slice = hashlib.md5()
    md5etag = ''
    
    chunk_hashes = list()
    slice_ready = False
    chunk_buf = bytearray()
    chunk_accum = 0
    bytes_read = 0
    
    with open(file_path, 'rb') as f, tqdm(total=file_size, unit='B', unit_divisor=1024, unit_scale=True, desc='Hashing') as pbar:
        while True:
            block = f.read(BLOCK_SIZE)
            if not block:
                break
            
            # Update all-in-one
            crc = zlib.crc32(block, crc)
            md5file.update(block)
            
            if not slice_ready:
                remain = max(0, 1024 * 256 - bytes_read)
                md5slice.update(block[:remain])
                if bytes_read + len(block) >= 1024 * 256:
                    slice_ready = True
            
            chunk_buf.extend(block)
            chunk_accum += len(block)
            
            if chunk_accum >= chunk_size:
                chunk_hash = hashlib.md5(chunk_buf).hexdigest()
                chunk_hashes.append(chunk_hash)
                chunk_buf.clear()
                chunk_accum = 0
            
            bytes_read += len(block)
            pbar.update(len(block))
        
        # Handle final chunk (if file size isn't multiple of chunk size)
        if chunk_buf:
            chunk_hash = hashlib.md5(chunk_buf).hexdigest()
            chunk_hashes.append(chunk_hash)
            chunk_buf.clear()
        
        crc = crc & 0xFFFFFFFF
        md5slice = md5slice.hexdigest()
        md5file = md5file.hexdigest()
        
        md5etag = md5file
        if len(chunk_hashes) > 1:
            md5etag = json.dumps(chunk_hashes, separators=(',', ':'))
            md5etag = hashlib.md5(md5etag.encode('utf-8')).hexdigest()
            md5etag += f'-{len(chunk_hashes)}'
    
    return {
        'size': file_size,
        'hash': {
            'crc32': crc,
            'slice': md5slice,
            'file': md5file,
            'etag': md5etag,
            'chunks': chunk_hashes,
        }
    }

class IndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)

def checkFolder(inputPath: Path):
    print(f':: Selected path: {inputPath}\n')
    
    if os.path.isdir(inputPath):
        for dirpath, dirnames, filenames in os.walk(inputPath):
            for file in filenames:
                if Path(file).suffix.lower() in ALLOWED_EXT:
                    file_path = Path(dirpath, file)
                    file_size = file_path.stat().st_size
                    tbfile_path = Path(f'{file_path}.tbhash')
                    
                    if tbfile_path.is_file():
                        print('TBHash File:', file_path.name)
                    elif file_size > get_chunk_size(0):
                        print('Hashing:', file_path.name)
                        get_hash = hash_file(file_path, file_size)
                        with open(f'{file_path}.tbhash', 'w', encoding='utf-8', newline='\n') as f:
                            f.write(yaml.dump(get_hash, Dumper=IndentDumper, indent=2, default_flow_style=False, sort_keys=False))
                    else:
                        print('File too small:', file_path.name)

# set folder
if len(sys.argv) < 2:
    inputPath = qtext(':: Folder: ', validate=PathValidator).ask()
    inputPath = inputPath.strip('\"')
else:
    inputPath = sys.argv[1]

# check path
if not os.path.isdir(inputPath):
    print(f':: Path is not a folder: "{inputPath}"!')
else:
    checkFolder(inputPath)

# end
if os.environ.get('isBatch') is None:
    qpause(message = '\n:: Press enter to continue...\n').ask()
