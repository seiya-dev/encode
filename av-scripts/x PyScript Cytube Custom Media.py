import json
import os
from urllib.parse import quote

def encode_url_path(url: str) -> str:
    if "://" in url:
        protocol, path = url.split("://", 1)
        encoded_path = "/".join(quote(part, safe="") for part in path.split("/"))
        return protocol + "://" + encoded_path
    else:
        return "/".join(quote(part, safe="") for part in url.split("/"))

def parse_duration(duration_str: str) -> int:
    parts = duration_str.strip().split(":")
    parts = [int(p) for p in parts]

    if len(parts) == 1:
        return parts[0]                                      # "45" = 45 seconds
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]                      # mm:ss
    elif len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]    # hh:mm:ss
    else:
        raise ValueError("Invalid duration format")

def generate_json_files():
    output_folder = "cm"
    os.makedirs(output_folder, exist_ok=True)

    base_title = input("Enter base title: ").strip()
    base_url = input("Enter base URL: ").strip()

    # Auto-add https://
    if not base_url.startswith("http://") and not base_url.startswith("https://"):
        base_url = "https://" + base_url

    # Auto-add trailing /
    if not base_url.endswith("/"):
        base_url += "/"

    # Encode base URL path
    base_url = encode_url_path(base_url)

    file_prefix_raw = input("Enter file prefix: ")  # do not strip
    file_prefix_encoded = quote(file_prefix_raw, safe="")

    # Duration input
    duration_input = input("Enter duration (0:00 or 00:00 or 0:00:00): ")
    duration_seconds = parse_duration(duration_input)

    start_ep = int(input("Enter starting episode number: ").strip())
    end_ep = int(input("Enter final episode number: ").strip())

    for ep in range(start_ep, end_ep + 1):
        ep_str = f"{ep:02d}"
        ep_str_encoded = quote(ep_str, safe="")

        # Title = readable filename
        title = f"{base_title} - {ep_str}"

        # Encoded filename part
        encoded_filename = f"{file_prefix_encoded}{ep_str_encoded}"

        sources = [
            {
                "url": f"{base_url}{encoded_filename}%20%5B720p%5D.mp4",
                "contentType": "video/mp4",
                "quality": 720
            },
            {
                "url": f"{base_url}{encoded_filename}%20%5B1080p%5D.mp4",
                "contentType": "video/mp4",
                "quality": 1080
            }
        ]

        data = {
            "title": title,
            "duration": duration_seconds,
            "live": False,
            "sources": sources
        }

        filename = os.path.join(output_folder, f"{title}.json")

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(f"Created: {filename}")

    print("All JSON files generated in folder 'cm/'.")

if __name__ == "__main__":
    generate_json_files()
