from PIL import ImageFont
import os
import sys

def find_system_font_dirs():
    if sys.platform.startswith('win'):
        WINDIR = os.environ.get('WINDIR', 'C:/Windows')
        return [
            os.path.join(WINDIR, 'Fonts'),
        ]
    elif sys.platform.startswith('darwin'):
        return [
            '/System/Library/Fonts',
            '/Library/Fonts',
            os.path.expanduser('~/Library/Fonts'),
        ]
    else:
        return [
            '/usr/share/fonts',
            '/usr/local/share/fonts',
            os.path.expanduser('~/.fonts'),
        ]

def get_fonts():
    font_dirs = find_system_font_dirs()
    font_list = []
    for font_dir in font_dirs:
        if os.path.isdir(font_dir):
            for root, _, files in os.walk(font_dir):
                for file in files:
                    if file.lower().endswith(('.ttf', '.otf')):
                        font_path = os.path.join(root, file)
                        try:
                            font = ImageFont.truetype(font_path)
                            font_list.append(font.getname()[0])
                        except Exception:
                            continue
    return sorted(set(font_list))

def parse_styles(subtitle_lines):
    style_list = []
    for line in subtitle_lines:
        if 'Style:' in line and ',' in line:
            parts = line.split(':', 1)
            if len(parts) >= 2:
                style_name = parts[1].split(',')[0].strip()
                style_list.append(style_name)
    return style_list

if __name__ == '__main__':
    subtitle_text = []
    # parse_styles(subtitle_text)
