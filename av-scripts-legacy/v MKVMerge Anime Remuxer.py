#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
import shutil
import mimetypes
import tempfile
import json
import questionary


def ask_settings():
    default_src = '.'
    default_out = '<same as source>'

    return {
        'src_dir': Path(questionary.text('Source directory:', default=default_src).ask()).expanduser().resolve(),
        'out_dir': Path(questionary.text('Output directory (default: same):', default=default_out).ask()).expanduser().resolve()
        if questionary.text('Output directory (default: same):', default=default_out).ask().strip() not in ('', default_out) else None,
        'video_title': questionary.text('Track title for VIDEO:', default='Video').ask(),
        'audio_lang': questionary.text('Language code for AUDIO:', default='ja').ask(),
        'sub_lang': questionary.text('Language code for SUBTITLES:', default='en').ask(),
        'sub_track_name': questionary.text('Track name for SUBTITLES:', default='English').ask(),
    }


def guess_mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(path.name)
    return mime or 'application/octet-stream'


def build_option_array(
    mkv: Path,
    subs: Path,
    chap: Path,
    fonts: list[Path],
    out_path: Path,
    video_title: str,
    audio_lang: str,
    sub_lang: str,
    sub_track_name: str
) -> list:
    args = [
        "--disable-track-statistics-tags",
        "--engage", "no_variable_data",
        "--no-date",
        "-o", str(out_path),
        "--no-global-tags",
        "--track-name", f"0:{video_title}",
        "--language", f"1:{audio_lang}",
        str(mkv),
        "--language", f"0:{sub_lang}",
        "--track-name", f"0:{sub_track_name}",
        str(subs),
        "--chapter-language", "eng",
        "--chapters", str(chap),
    ]
    for font in fonts:
        args.extend([
            "--attachment-mime-type", guess_mime(font),
            "--attachment-name", font.name,
            "--attach-file", str(font),
        ])
    return args


def mux_folder(settings):
    src_dir: Path = settings['src_dir']
    out_dir: Path | None = settings['out_dir']

    video_title = settings['video_title']
    audio_lang = settings['audio_lang']
    sub_lang = settings['sub_lang']
    sub_track_name = settings['sub_track_name']

    if not src_dir.is_dir():
        sys.exit(f'❌ Source directory not found: {src_dir}')

    mkvmerge = shutil.which('mkvmerge')
    if not mkvmerge:
        sys.exit('❌ "mkvmerge" not found in PATH.')

    subs_dir = src_dir / 'subtitles'
    chapters_dir = src_dir / 'chapters'
    fonts_dir = src_dir / 'fonts'

    fonts = sorted(fonts_dir.glob('*.ttf')) + sorted(fonts_dir.glob('*.otf')) if fonts_dir.exists() else []

    mkvs = sorted(src_dir.glob('*.mkv'))
    if not mkvs:
        sys.exit('❌ No .mkv files found.')

    print(f'\n📂 Scanning {src_dir}  (writing to {out_dir or "same location"})\n')

    for mkv in mkvs:
        stem = mkv.stem
        subs = subs_dir / f'{stem}.ass'
        chap = chapters_dir / f'{stem}.chapters.txt'

        if not subs.exists() or not chap.exists():
            print(f'⏩ {stem}: skipped (missing .ass or .chapters.txt)')
            continue

        dest_dir = out_dir or mkv.parent
        dest_dir.mkdir(parents=True, exist_ok=True)
        out_path = dest_dir / f'{stem}_muxed.mkv'

        args = build_option_array(
            mkv, subs, chap, fonts, out_path,
            video_title, audio_lang, sub_lang, sub_track_name
        )

        # Write args to a valid JSON array
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.json', encoding='utf-8') as f:
            json.dump(args, f, ensure_ascii=False, indent=2)
            option_file = Path(f.name)

        print(f'→ mkvmerge @{option_file}')
        try:
            subprocess.run([mkvmerge, f'@{option_file}'], check=True)
            print(f'✓  {out_path}')
        except subprocess.CalledProcessError:
            print(f'❌ Error muxing {mkv.name}')
        finally:
            option_file.unlink()

    print('\n🎉 All done!')


if __name__ == '__main__':
    try:
        settings = ask_settings()
        mux_folder(settings)
    except KeyboardInterrupt:
        print('\nAborted by user.')
