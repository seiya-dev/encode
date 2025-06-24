#!/usr/bin/env python3
"""
convert_chapters.py – convert Matroska XML chapter files to OGM format.

USAGE
-----
# One file → stdout
python convert_chapters.py movie_chapters.xml

# One file → chapters.txt
python convert_chapters.py movie_chapters.xml -o chapters.txt

# Convert every *.xml in a folder (non-recursive)
python convert_chapters.py /path/to/chapters_dir

# Recursive folder walk, writing *.txt alongside XMLs
python convert_chapters.py /path/to/chapters_dir --recursive

# Folder walk, but put results in a separate directory
python convert_chapters.py /path/to/chapters_dir -O /path/to/outdir --recursive
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
import xml.etree.ElementTree as ET

# ────────────────────────── XML → list[(timestamp, title)] ─────────────────────
def parse_chapters(xml_path: Path) -> list[tuple[str, str]]:
    """Return [(HH:MM:SS.mmm, title), …] from the first EditionEntry."""
    root = ET.parse(xml_path).getroot()
    ns   = {'n': root.tag.partition('}')[0].strip('{')} if '}' in root.tag else {}
    atoms = root.findall('.//n:ChapterAtom', ns) if ns else root.findall('.//ChapterAtom')
    chapters: list[tuple[str, str]] = []

    for atom in atoms:
        t_start = atom.find('n:ChapterTimeStart', ns) if ns else atom.find('ChapterTimeStart')
        if t_start is None:
            continue
        title_el = atom.find('.//n:ChapterString', ns) if ns else atom.find('.//ChapterString')
        title    = (title_el.text or '').strip() if title_el is not None else ''
        hhmmss, *nano = t_start.text.split('.')
        millis   = int(nano[0][:3]) if nano else 0
        chapters.append((f'{hhmmss}.{millis:03d}', title))
    return chapters

# ───────────────────────────── list → OGM text ────────────────────────────────
def to_ogm(chaps: list[tuple[str, str]]) -> str:
    lines = []
    for idx, (ts, name) in enumerate(chaps, 1):
        tag = f'{idx:02d}'
        lines += [f'CHAPTER{tag}={ts}', f'CHAPTER{tag}NAME={name}']
    return '\n'.join(lines) + '\n'

# ───────────────────────────────── CLI glue ────────────────────────────────────
def convert_file(xml_path: Path, dest_path: Path | None):
    chapters = parse_chapters(xml_path)
    if not chapters:
        print(f'[warning] {xml_path}: no ChapterAtom elements found.', file=sys.stderr)
        return
    ogm_text = to_ogm(chapters)
    if dest_path:
        dest_path.write_text(ogm_text, encoding='utf-8')
    else:
        print(ogm_text, end='')

def gather_xmls(path: Path, recursive: bool) -> list[Path]:
    if path.is_file():
        return [path]
    pattern = '**/*.xml' if recursive else '*.xml'
    return sorted(p for p in path.glob(pattern) if p.is_file())

def main():
    ap = argparse.ArgumentParser(description='Convert XML chapters to OGM format')
    ap.add_argument('input', type=Path, help='XML file or directory of XML files')
    ap.add_argument('-o', '--output', type=Path,
                    help='Output file (for single-file mode) or directory (for folder mode).')
    ap.add_argument('-r', '--recursive', action='store_true',
                    help='When input is a directory, search sub-directories too.')
    args = ap.parse_args()

    xml_files = gather_xmls(args.input, args.recursive)
    if not xml_files:
        sys.exit('No XML files found.')

    # Single-file mode
    if len(xml_files) == 1:
        out = args.output
        if out and out.is_dir():
            out = out / (xml_files[0].stem + '.txt')
        convert_file(xml_files[0], out)
        return

    # Folder / batch mode
    out_dir = args.output
    if out_dir and not out_dir.exists():
        out_dir.mkdir(parents=True)
    for x in xml_files:
        target = (out_dir / x.with_suffix('.txt').name) if out_dir else x.with_suffix('.txt')
        convert_file(x, target)
        print(f'[{x}] → [{target}]')

if __name__ == '__main__':
    main()
