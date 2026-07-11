#!/usr/bin/env python3

import os
import shutil
import sys

print('NOTE: attachments folder should be sub folder!')

inDir = input(':: Dir: ') if len(sys.argv) < 2 else sys.argv[1]

inDirAtt = os.path.abspath(f'{inDir}/attachments/')
outDirFonts = os.path.abspath(f'{inDir}/fonts/')
outDirSubs = os.path.abspath(f'{inDir}/subtitles/')
outDirXML = os.path.abspath(f'{inDir}/chap_tags/')

os.makedirs(outDirFonts, exist_ok=True)
os.makedirs(outDirSubs, exist_ok=True)
os.makedirs(outDirXML, exist_ok=True)

extFonts = ['.ttf', '.ttc', '.otf', '.woff', '.woff2']
extSubs = ['.ass', '.srt']
extXml = ['.xml']

for root, _, files in os.walk(inDirAtt):
    for file in files:
        if file.lower().endswith(tuple(extFonts)):
            src = os.path.join(os.path.sep, root, file)
            out = os.path.join(os.path.sep, outDirFonts, file)
            print(f':: {src} -> {out}')
            shutil.move(src, out)

for root, _, files in os.walk(inDirAtt):
    for file in files:
        if file.lower().endswith(tuple(extSubs)):
            src = os.path.join(os.path.sep, root, file)
            ass = src.split(os.path.sep)[-2:]
            out = os.path.join(os.path.sep, outDirSubs, '_'.join(ass))
            print(f':: {src} -> {out}')
            shutil.move(src, out)

for root, _, files in os.walk(inDirAtt):
    for file in files:
        if file.lower().endswith(tuple(extXml)):
            src = os.path.join(os.path.sep, root, file)
            ass = src.split(os.path.sep)[-2:]
            out = os.path.join(os.path.sep, outDirXML, '_'.join(ass))
            print(f':: {src} -> {out}')
            shutil.move(src, out)


# end
if os.environ.get('ISBATCH') is None:
    input('\n:: Press any key to continue...\n')
