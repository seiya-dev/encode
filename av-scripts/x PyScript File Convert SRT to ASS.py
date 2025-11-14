#!/usr/bin/env python3

# set libs
import os
import re
import sys

from pathlib import Path
from pathlib import PurePath

try:
    import questionary
    from questionary import Choice, Validator, ValidationError
    from _encHelper import PathValidator
except ModuleNotFoundError:
    print(':: Please install "questionary" module: pip install questionary')
    input(':: Press enter to continue...\n')
    exit()

ASS_HEADER = """[Script Info]
Title: Default
Original Translation: 
Original Editing: 
Original Timing: 
Synch Point: 
Script Updated By: 
Update Details: 
ScriptType: v4.00+
PlayResX: 640
PlayResY: 360
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Roboto Medium,26,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1.3,0,2,20,20,23,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

TIMECODE_RE = re.compile(
    r"^\s*(\d{1,2}):([0-5]\d):([0-5]\d)[,\.](\d{1,3})\s*-->\s*(\d{1,2}):([0-5]\d):([0-5]\d)[,\.](\d{1,3})\s*$"
)

def to_ms(h, m, s, ms):
    return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms.ljust(3, "0")[:3])

def ms_to_ass_time(ms):
    # ASS wants H:MM:SS.cc (centiseconds)
    cs = int(round(ms / 10.0))
    h = cs // (100 * 3600)
    cs %= 100 * 3600
    m = cs // (100 * 60)
    cs %= 100 * 60
    s = cs // 100
    c = cs % 100
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"

def srt_block_iter(text):
    text = text.replace("\ufeff", "")
    chunks = re.split(r"(?:\r?\n){2,}", text, flags=re.MULTILINE)
    for chunk in chunks:
        if chunk.strip():
            yield chunk

def srt_to_events(srt_text):
    # Returns list of (start_ms, end_ms, text_lines) where text_lines is a list of strings.
    events = []
    for block in srt_block_iter(srt_text):
        lines = block.splitlines()
        if not lines:
            continue

        # Optional numeric index on first line
        idx = 0
        if re.match(r"^\s*\d+\s*$", lines[0]):
            idx = 1

        if idx >= len(lines):
            continue

        m = TIMECODE_RE.match(lines[idx].strip())
        if not m:
            # Not a valid subtitle block; skip
            continue

        h1, m1, s1, ms1, h2, m2, s2, ms2 = m.groups()
        start_ms = to_ms(h1, m1, s1, ms1)
        end_ms = to_ms(h2, m2, s2, ms2)

        text_lines = [ln.rstrip("\r") for ln in lines[idx + 1 :]]
        # Drop trailing empty lines
        while text_lines and not text_lines[-1].strip():
            text_lines.pop()

        events.append((start_ms, end_ms, text_lines))
    return events

def html_to_ass(text):
    # Convert a subset of HTML-like tags to ASS override tags.
    # Handles <i>, <b>, <u>, and their closing forms; strips other tags.
    # Basic replacements for italics/bold/underline
    repl = [
        (re.compile(r"<\s*i\s*>", re.IGNORECASE), r"{\\i1}"),
        (re.compile(r"<\s*/\s*i\s*>", re.IGNORECASE), r"{\\i0}"),
        (re.compile(r"<\s*b\s*>", re.IGNORECASE), r"{\\b1}"),
        (re.compile(r"<\s*/\s*b\s*>", re.IGNORECASE), r"{\\b0}"),
        (re.compile(r"<\s*u\s*>", re.IGNORECASE), r"{\\u1}"),
        (re.compile(r"<\s*/\s*u\s*>", re.IGNORECASE), r"{\\u0}"),
        (re.compile(r"<\s*br\s*/?\s*>", re.IGNORECASE), r"\\N"),
    ]
    for pat, rep in repl:
        text = pat.sub(rep, text)
    # Strip any other tags
    text = re.sub(r"</?\s*\w+[^>]*>", "", text)
    return text

def escape_ass_text(text):
    # already converted <br> to \N; now handle actual newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", r"\N")
    return text

def build_dialogue_line(start_ms, end_ms, raw_lines):
    # Join lines with explicit newline first (becomes \N later)
    raw_text = "\n".join(raw_lines)
    raw_text = html_to_ass(raw_text)
    ass_text = escape_ass_text(raw_text)

    start = ms_to_ass_time(start_ms)
    end = ms_to_ass_time(end_ms)

    # Layer, Start, End, Style, Name, ML, MR, MV, Effect, Text
    return f"Dialogue: 0,{start},{end},Default,,0,0,0,,{ass_text}"

def convert_srt_path(srt_path: Path, out_path: Path = None):
    content = srt_path.read_text(encoding="utf-8", errors="replace")
    events = srt_to_events(content)
    lines = [ASS_HEADER]
    for (st, et, txt_lines) in events:
        lines.append(build_dialogue_line(st, et, txt_lines))
    out = out_path or srt_path.with_suffix(".ass")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out

def convertFile(file: Path):
    file = Path(file)
    if file.suffix.lower() != ".srt":
        raise ValueError(f'Not an .srt file: "{file}"')
    out = convert_srt_path(file)
    print(f':: Converted: "{file.name}" -> "{out.name}"')

def convertFolder(inputPath: Path):
    print(f'\n:: Selected path: {os.path.abspath(inputPath)}')
    for file in os.listdir(inputPath):
        file = os.path.join(inputPath, file)
        if file.lower().endswith('.srt'):
            convertFile(file)

# set folder
if len(sys.argv) < 2:
    inputPath = questionary.text(':: Folder/File: ', validate=PathValidator).ask()
    inputPath = inputPath.strip('\"')
else:
    inputPath = sys.argv[1]

# check path
try:
    if not os.path.isdir(inputPath):
        if os.path.isfile(inputPath) and PurePath(inputPath).suffix.lower() == '.srt':
            convertFile(inputPath)
        else:
            print(f':: Path is not a srt file or folder: "{inputPath}"!')
    else:
        convertFolder(inputPath)
except Exception as err:
    print(f':: Something goes wrong...')
    print(f':: {type(err).__name__}: {err}')

# end
if os.environ.get('isBatch') is None:
    questionary.press_any_key_to_continue(message = '\n:: Press enter to continue...\n').ask()
