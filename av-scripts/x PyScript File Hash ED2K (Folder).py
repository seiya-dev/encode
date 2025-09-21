#!/usr/bin/env python3

import os
import sys
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
    from Cryptodome.Hash import MD4
    from tqdm import tqdm
except ModuleNotFoundError as errorModule:
    moduleNotFound(str(errorModule))
    exit()

print(':: File Hash: ED2K ::')
ALLOWED_EXT = ('.mkv', '.mp4', '.avi', '.mka', '.flac', '.wav')
CHUNK_SIZE = 1024 * 9500 # 9500 KiB

def md4(data):
    h = MD4.new()
    h.update(data)
    return h.digest()

def ed2k_hash(file_path, file_size):
    chunk_hashes = []
    
    with open(file_path, 'rb') as f, tqdm(total=file_size, unit='B', unit_divisor=1024, unit_scale=True, desc='Hashing') as pbar:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            chunk_hashes.append(md4(chunk))
            pbar.update(len(chunk))
    
    if len(chunk_hashes) == 1:
        return chunk_hashes[0].hex()
    else:
        return md4(b''.join(chunk_hashes)).hex()

def hashFile(file_path: Path):
    file_path = Path(file_path)
    file_size = os.path.getsize(file_path)
    
    file_name = file_path.name
    print('Hashing:', file_name)
    hash_hex = ed2k_hash(file_path, file_size)
    
    return f"ed2k://|file|{file_name}|{file_size}|{hash_hex}|/"

def checkFolder(inputPath: Path):
    print(f':: Selected path: {inputPath}\n')
    hashes = list()
    
    if os.path.isdir(inputPath):
        for dirpath, dirnames, filenames in os.walk(inputPath):
            for file in filenames:
                if Path(file).suffix.lower() in ALLOWED_EXT:
                    get_hash = hashFile(Path(dirpath, file))
                    hashes.append(get_hash + '\n')
            hashes.append('\n')
        
        with open(
            str(Path(inputPath, '.ed2k.txt')),
            'a',
            encoding='utf-8',
            newline='\n'
        ) as f:
            f.writelines(hashes)

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
