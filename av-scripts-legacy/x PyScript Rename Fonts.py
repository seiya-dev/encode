import os
import re
import hashlib
import questionary
from fontTools.ttLib import TTFont
from collections import defaultdict

def get_name_record(font, nameID):
    for record in font['name'].names:
        if record.nameID == nameID and record.platformID == 3 and record.langID == 0x409:
            try:
                return record.string.decode('utf-16-be')
            except:
                continue
    for record in font['name'].names:
        if record.nameID == nameID:
            try:
                return record.string.decode('utf-16-be') if b'\x00' in record.string else record.string.decode('utf-8')
            except:
                continue
    return None

def get_font_name_and_version(font_path):
    try:
        font = TTFont(font_path)
        postscript = get_name_record(font, 6)
        version_raw = get_name_record(font, 5)
        family = get_name_record(font, 1)
        subfamily = get_name_record(font, 2)
        font.close()

        if not postscript and family:
            postscript = f"{family}-{subfamily or 'Regular'}"

        version = "0.0"
        if version_raw:
            match = re.search(r'(\d+(\.\d+)+)', version_raw)
            version = match.group(1) if match else "0.0"

        return postscript, version
    except Exception as e:
        print(f"❌ Error reading {font_path}: {e}")
        return None, None

def calculate_checksum(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def ask_for_folder():
    return questionary.text("📂 Enter the path to the folder with .ttf/.otf files:").ask()

def get_unique_filename(directory, base_name, ext, alt_count=0):
    if alt_count == 0:
        filename = f"{base_name}{ext}"
    else:
        filename = f"{base_name}_alt{alt_count}{ext}"

    while os.path.exists(os.path.join(directory, filename)):
        alt_count += 1
        filename = f"{base_name}_alt{alt_count}{ext}"

    return filename

def rename_fonts_safely(directory):
    if not os.path.isdir(directory):
        print("❌ Invalid directory")
        return

    seen_hashes = {}
    seen_names = defaultdict(list)
    print(f"\n📁 Renaming fonts in: {directory}\n")

    for filename in os.listdir(directory):
        if not filename.lower().endswith((".ttf", ".otf")):
            continue

        filepath = os.path.join(directory, filename)
        file_hash = calculate_checksum(filepath)

        # Skip if exact duplicate already processed
        if file_hash in seen_hashes:
            print(f"🔂 Exact duplicate skipped: {filename} (same as {seen_hashes[file_hash]})")
            continue

        ps_name, version = get_font_name_and_version(filepath)
        if not ps_name:
            print(f"❌ Could not extract usable metadata from: {filename}")
            continue

        ext = os.path.splitext(filename)[1].lower()
        safe_ps = ps_name.replace(" ", "_").replace("/", "_")
        version_str = f"_v{version}" if version else ""
        base_name = f"{safe_ps}{version_str}"
        expected_name = f"{base_name}{ext}"

        # Check if filename already matches expected name
        clean_current = filename.lower().replace(" ", "").replace("_", "")
        clean_expected = expected_name.lower().replace(" ", "").replace("_", "")

        if clean_current.startswith(clean_expected.replace(ext, "")):
            # Even if name matches, confirm if hash is unique
            duplicate = False
            for existing in seen_names[f"{ps_name}|{version}"]:
                existing_path = os.path.join(directory, existing)
                if os.path.exists(existing_path):
                    if calculate_checksum(existing_path) == file_hash:
                        duplicate = True
                        break
            if duplicate:
                print(f"⏩ Already correctly named: {filename}")
                continue
            else:
                print(f"⚠️ Name matches expected but content is different: {filename}")
                # continue with renaming below

        # Assign unique name
        alt_count = len(seen_names[f"{ps_name}|{version}"])
        new_filename = get_unique_filename(directory, base_name, ext, alt_count)
        new_filepath = os.path.join(directory, new_filename)

        os.rename(filepath, new_filepath)
        seen_hashes[file_hash] = new_filename
        seen_names[f"{ps_name}|{version}"].append(new_filename)

        print(f"✅ Renamed: {filename} → {new_filename}")

if __name__ == "__main__":
    folder = ask_for_folder()
    if folder:
        rename_fonts_safely(folder)

    input("\n✅ Done! Press Enter to exit...")
