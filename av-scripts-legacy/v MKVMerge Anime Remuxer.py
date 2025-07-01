#!/usr/bin/env python3
'''
Batch-mux every *.mkv* in a source folder, adding matching subtitle,
chapter and font files via **mkvmerge**. Prompts are handled with
**questionary**, so no command-line flags are needed.

Directory layout (required):

SRC/
├── subtitles/   # ⟶  <basename>.ass
├── chapters/    # ⟶  <basename>.chapters.txt   (language hard-coded: eng)
├── fonts/       # (optional) *.ttf / *.otf attached to every output
└── <basename>.mkv

The script now also lets you:
* set a **Video track title** (name of track 0 in the source MKV)
* choose an **Audio track language** (applied to track 1 in the source MKV)
* pick **Subtitle language + track name** (for the external .ass file)

Extra mkvmerge switches added globally:
    --disable-track-statistics-tags
    --engage no_variable_data
    --no-date

Install:
    pip install questionary
'''

from pathlib import Path
import subprocess
import sys
import shutil
import mimetypes
import questionary

# ───────────────────────── configuration via prompts ──────────────────────────

def ask_settings():
    '''Collect settings interactively via questionary prompts.'''  # noqa: D401
    default_src = '.'
    default_out = '<same as source>'

    default_video_title = 'Video'
    default_audio_lang = 'ja'
    default_sub_lang = 'en'
    default_sub_track_name = 'English'

    src_dir = Path(
        questionary.text(
            'Source directory (contains MKV files and sub-folders):',
            default=default_src,
        ).ask()
    ).expanduser().resolve()

    out_dir_answer = questionary.text(
        f'Output directory (default: {default_out}):',
        default=default_out,
    ).ask()

    out_dir = (
        None
        if out_dir_answer.strip() in ('', default_out)
        else Path(out_dir_answer).expanduser().resolve()
    )

    video_title = questionary.text(
        'Track title for VIDEO (track 0):',
        default=default_video_title,
    ).ask()

    audio_lang = questionary.text(
        'Language code for AUDIO (track 1):',
        default=default_audio_lang,
    ).ask()

    sub_lang = questionary.text(
        'Language code for SUBTITLES:',
        default=default_sub_lang,
    ).ask()

    sub_track_name = questionary.text(
        'Track name for SUBTITLES:',
        default=default_sub_track_name,
    ).ask()

    return {
        'src_dir': src_dir,
        'out_dir': out_dir,
        'video_title': video_title,
        'audio_lang': audio_lang,
        'sub_lang': sub_lang,
        'sub_track_name': sub_track_name,
    }


# ────────────────────────── mkvmerge wrapper helpers ──────────────────────────

def guess_mime(path: Path) -> str:
    '''Guess a reasonable MIME type for attachments.'''
    mime, _ = mimetypes.guess_type(path.name)
    return mime or 'application/octet-stream'


def build_cmd(
    mkvmerge: str,
    base: Path,
    subs: Path,
    chap: Path,
    fonts: list[Path],
    out_path: Path,
    video_title: str,
    audio_lang: str,
    sub_lang: str,
    sub_track_name: str,
) -> list[str]:
    '''Compose the mkvmerge command list for a single episode.'''
    cmd: list[str] = [
        mkvmerge,
        '--disable-track-statistics-tags',
        '--engage', 'no_variable_data',
        '--no-date',
        '-o', str(out_path),
        '--no-global-tags',
        # ── source MKV: set video title & audio language ──
        '--track-name', f'0:{video_title}',
        '--language', f'1:{audio_lang}',
        str(base),
        # ── external subtitles ──
        '--language', f'0:{sub_lang}',
        '--track-name', f'0:{sub_track_name}',
        str(subs),
        # ── chapters with fixed lang ──
        '--chapter-language', 'eng',
        '--chapters', str(chap),
    ]

    # ── font attachments ──
    for font in fonts:
        cmd.extend([
            '--attachment-mime-type', guess_mime(font),
            '--attachment-name', font.name,
            '--attach-file', str(font),
        ])

    return cmd


# ───────────────────────────── muxing routine ────────────────────────────────

def mux_folder(settings) -> None:
    '''Mux every MKV in *src_dir* using side-files from sub-folders.'''
    src_dir: Path = settings['src_dir']
    out_dir: Path | None = settings['out_dir']

    video_title: str = settings['video_title']
    audio_lang: str = settings['audio_lang']
    sub_lang: str = settings['sub_lang']
    sub_track_name: str = settings['sub_track_name']

    if not src_dir.is_dir():
        sys.exit(f'❌ Source directory not found: {src_dir}')

    mkvmerge = shutil.which('mkvmerge')
    if not mkvmerge:
        sys.exit('❌ "mkvmerge" not found in PATH. Install MKVToolNix first.')

    # Prepare sub-folder paths
    subs_dir = src_dir / 'subtitles'
    chapters_dir = src_dir / 'chapters'
    fonts_dir = src_dir / 'fonts'

    # Gather font attachments once (global for every episode)
    fonts: list[Path] = []
    if fonts_dir.is_dir():
        fonts = sorted(fonts_dir.glob('*.ttf')) + sorted(fonts_dir.glob('*.otf'))

    mkvs = sorted(src_dir.glob('*.mkv'))
    if not mkvs:
        sys.exit('❌ No .mkv files found in the source directory.')

    print(
        f'\n📂 Scanning {src_dir}'
        f'  (writing to {out_dir or "same location"})\n'
    )

    for mkv in mkvs:
        stem = mkv.stem
        subs = subs_dir / f'{stem}.ass'
        chap = chapters_dir / f'{stem}.chapters.txt'

        if not subs.exists() or not chap.exists():
            print(f'⏩  {stem}: skipped (missing .ass or .chapters.txt)')
            continue

        dest_dir = out_dir or mkv.parent
        dest_dir.mkdir(parents=True, exist_ok=True)
        out_path = dest_dir / f'{stem}_muxed.mkv'

        cmd = build_cmd(
            mkvmerge,
            mkv,
            subs,
            chap,
            fonts,
            out_path,
            video_title=video_title,
            audio_lang=audio_lang,
            sub_lang=sub_lang,
            sub_track_name=sub_track_name,
        )

        print('→', ' '.join(cmd))
        subprocess.run(cmd, check=True)
        print(f'✓  {out_path}')

    print('\n🎉 All done!')


# ────────────────────────────────── main ──────────────────────────────────────

if __name__ == '__main__':
    try:
        settings = ask_settings()
        mux_folder(settings)
    except KeyboardInterrupt:
        print('\nAborted by user.')
