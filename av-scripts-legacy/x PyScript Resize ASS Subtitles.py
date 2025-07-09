import re
from pathlib import Path
import questionary

TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080

def scale_override_tags(line, scale_x, scale_y):
    line = re.sub(r'\\fs([\d.]+)', lambda m: f"\\fs{float(m.group(1)) * scale_y:.2f}", line)

    line = re.sub(
        r'\\pos\(([\d.]+),([\d.]+)\)',
        lambda m: f"\\pos({float(m.group(1)) * scale_x:.2f},{float(m.group(2)) * scale_y:.2f})",
        line
    )

    def scale_move(m):
        x1 = float(m.group(1)) * scale_x
        y1 = float(m.group(2)) * scale_y
        x2 = float(m.group(3)) * scale_x
        y2 = float(m.group(4)) * scale_y
        if m.group(5):
            return f"\\move({x1:.2f},{y1:.2f},{x2:.2f},{y2:.2f},{m.group(5)},{m.group(6)})"
        return f"\\move({x1:.2f},{y1:.2f},{x2:.2f},{y2:.2f})"

    line = re.sub(r'\\move\(([\d.]+),([\d.]+),([\d.]+),([\d.]+)(?:,([\d]+),([\d]+))?\)', scale_move, line)

    line = re.sub(
        r'\\org\(([\d.]+),([\d.]+)\)',
        lambda m: f"\\org({float(m.group(1)) * scale_x:.2f},{float(m.group(2)) * scale_y:.2f})",
        line
    )

    def scale_clip(m):
        coords = m.group(2).split(',')
        if len(coords) == 4:
            try:
                scaled = [
                    float(coords[0]) * scale_x,
                    float(coords[1]) * scale_y,
                    float(coords[2]) * scale_x,
                    float(coords[3]) * scale_y
                ]
                return f"\\{m.group(1)}clip({','.join(f'{c:.2f}' for c in scaled)})"
            except ValueError:
                return m.group(0)
        return m.group(0)

    line = re.sub(r'\\(i?)clip\(([^)]+)\)', scale_clip, line)

    return line

def parse_resolution(lines):
    res_x = res_y = None
    for line in lines:
        if line.startswith("PlayResX:"):
            res_x = int(line.split(":")[1].strip())
        elif line.startswith("PlayResY:"):
            res_y = int(line.split(":")[1].strip())
    return res_x, res_y

def process_file(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    res_x, res_y = parse_resolution(lines)
    if not res_x or not res_y:
        print(f"⚠ Skipping {file_path.name} (missing PlayResX/Y)")
        return

    scale_x = TARGET_WIDTH / res_x
    scale_y = TARGET_HEIGHT / res_y

    output_lines = []
    in_styles = in_events = False

    for line in lines:
        if line.strip().startswith("[V4+ Styles]"):
            in_styles, in_events = True, False
        elif line.strip().startswith("[Events]"):
            in_styles, in_events = False, True

        if line.startswith("PlayResX:"):
            output_lines.append(f"PlayResX: {TARGET_WIDTH}\n")
        elif line.startswith("PlayResY:"):
            output_lines.append(f"PlayResY: {TARGET_HEIGHT}\n")
        elif in_styles and line.startswith("Style:"):
            parts = line.strip().split(",")
            try:
                parts[2] = str(round(float(parts[2]) * scale_y))    # Font size
                parts[20] = str(round(float(parts[20]) * scale_x))  # MarginL
                parts[21] = str(round(float(parts[21]) * scale_x))  # MarginR
                parts[22] = str(round(float(parts[22]) * scale_y))  # MarginV
                output_lines.append(",".join(parts) + "\n")
            except (IndexError, ValueError) as e:
                print(f"⚠ Malformed style line in {file_path.name}: {e}")
                output_lines.append(line)
        elif in_events and line.startswith("Dialogue:"):
            scaled_line = scale_override_tags(line, scale_x, scale_y)
            output_lines.append(scaled_line)
        else:
            output_lines.append(line)

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(output_lines)

    print(f"✔ Overwritten: {file_path.name}")

def main():
    folder = questionary.text("Enter path to folder with .ass files:", default=".").ask()
    folder_path = Path(folder).resolve()

    if not folder_path.exists() or not folder_path.is_dir():
        print(f"❌ Invalid folder: {folder_path}")
        return

    ass_files = list(folder_path.glob("*.ass"))
    if not ass_files:
        print("❌ No .ass files found in that folder.")
        return

    for f in ass_files:
        process_file(f)

    print("\n🎉 All .ass files have been resized and overwritten.")

if __name__ == "__main__":
    main()
