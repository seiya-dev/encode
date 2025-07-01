#!/usr/bin/env python3
'''
x Convert Chapters (XML to TXT).py – Convert Matroska XML chapter files to OGM (TXT) format.

USAGE
-----
# Single file → filename.chapters.txt
python '<scriptfile>.py' movie.xml

# No arguments → interactive file/folder picker
python '<scriptfile>.py'

# Directory → every *.xml converted to *.chapters.txt in-place
python '<scriptfile>.py' /path/to/folder
'''

from __future__ import annotations
from pathlib import Path
import xml.etree.ElementTree as ET
import sys

try:
    import questionary
except ImportError:
    print('Please install questionary: pip install questionary')
    sys.exit(1)

def parse_chapters(xml_path: Path) -> list[tuple[str, str]]:
    root = ET.parse(xml_path).getroot()
    ns = {'n': root.tag.partition('}')[0].strip('{')} if '}' in root.tag else {}
    atoms = root.findall('.//n:ChapterAtom', ns) if ns else root.findall('.//ChapterAtom')
    chapters: list[tuple[str, str]] = []

    for atom in atoms:
        t_start = atom.find('n:ChapterTimeStart', ns) if ns else atom.find('ChapterTimeStart')
        if t_start is None:
            continue
        title_el = atom.find('.//n:ChapterString', ns) if ns else atom.find('.//ChapterString')
        title = (title_el.text or '').strip() if title_el is not None else ''
        hhmmss, *nano = t_start.text.split('.')
        millis = int(nano[0][:3]) if nano else 0
        chapters.append((f'{hhmmss}.{millis:03d}', title))
    return chapters

def to_ogm(chaps: list[tuple[str, str]]) -> str:
    lines = []
    for idx, (ts, name) in enumerate(chaps, 1):
        tag = f'{idx:02d}'
        lines += [f'CHAPTER{tag}={ts}', f'CHAPTER{tag}NAME={name}']
    return '\n'.join(lines) + '\n'

def convert_file(xml_path: Path, dest_path: Path):
    chapters = parse_chapters(xml_path)
    if not chapters:
        print(f'[warning] {xml_path}: no ChapterAtom elements found.', file=sys.stderr)
        return
    ogm_text = to_ogm(chapters)
    dest_path.write_text(ogm_text, encoding='utf-8')

def out_path_for(xml_file: Path) -> Path:
    return xml_file.with_name(xml_file.stem + '.chapters.txt')

def main():
    import argparse
    ap = argparse.ArgumentParser(description='Convert Matroska XML chapters to OGM TXT format')
    ap.add_argument('input', nargs='?', type=Path, help='XML file or directory containing XML files')
    args = ap.parse_args()

    input_path = args.input

    if not input_path:
        input_str = questionary.path('Select XML file or folder:').ask()
        if not input_str:
            print('No input provided.')
            questionary.press_any_key_to_continue().ask()
            return
        input_path = Path(input_str)

    if not input_path.exists():
        print(f'Input does not exist: {input_path}')
        questionary.press_any_key_to_continue().ask()
        return

    if input_path.is_file():
        convert_file(input_path, out_path_for(input_path))

    elif input_path.is_dir():
        xml_files = sorted(p for p in input_path.glob('*.xml') if p.is_file())
        if not xml_files:
            print('No XML files found in directory.')
            questionary.press_any_key_to_continue().ask()
            return
        for x in xml_files:
            out = out_path_for(x)
            convert_file(x, out)
            print(f'[{x.name}] → [{out.name}]')
    else:
        print('Input must be a file or directory.')
        questionary.press_any_key_to_continue().ask()
        return

    questionary.press_any_key_to_continue().ask()

if __name__ == '__main__':
    main()
