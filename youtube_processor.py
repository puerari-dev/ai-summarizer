import re
import yt_dlp

def get_video_description(url: str) -> str:
    """
    Fetches the video description from YouTube using yt_dlp.
    """
    ydl_opts = {'quiet': True, 'skip_download': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get("description", "")

def extract_timestamps_from_description(description: str) -> list:
    """
    Extracts timestamps and labels from the video description.
    Expected format: "00:00 Section Title"
    Returns a list of tuples (timestamp_in_seconds, label).
    """
    pattern = r'(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)'
    matches = re.findall(pattern, description)
    timestamps = []
    for time_str, label in matches:
        parts = time_str.split(":")
        if len(parts) == 3:
            seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            seconds = int(parts[0]) * 60 + int(parts[1])
        else:
            continue
        # Clean label for filenames
        clean_label = re.sub(r'[^a-zA-Z0-9_]', '', label.strip().replace(" ", "_"))
        timestamps.append((seconds, clean_label))
    return timestamps
