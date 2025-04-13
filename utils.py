import re
import ffmpeg

def clean_filename(s: str) -> str:
    """
    Cleans up a string to be used as a valid file name.
    Replaces spaces with underscores and removes invalid characters.
    """
    s = s.replace(" ", "_")
    return re.sub(r'[^a-zA-Z0-9_]', '', s)

def save_markdown(filename: str, content: str):
    """
    Saves given content to a Markdown file.
    """
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

def get_audio_duration(audio_path: str) -> float:
    """
    Returns the duration of the audio file in seconds.
    """
    try:
        probe = ffmpeg.probe(audio_path)
        return float(probe['format']['duration'])
    except Exception as e:
        print(f"Error getting duration: {e}")
        return 0.0