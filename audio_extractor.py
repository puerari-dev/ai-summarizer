import ffmpeg
import yt_dlp
import os
from utils import clean_filename

def download_youtube_audio(url: str, output_filename: str = "temp_media/output.mp3") -> tuple[bool, str]:
    """
    Downloads audio from a YouTube URL and saves as a MP3 file.
    Returns (success: bool, cleaned_title: str).
    """
    os.makedirs("temp_media", exist_ok=True)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_filename.replace('.mp3', ''),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '96',
        }],
        'quiet': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'output')
            return (True, title)
    except Exception as e:
        print(f"Error downloading YouTube audio: {e}")
        return (False, "")

def extract_audio_from_video(video_path: str, output_filename: str = "temp_media/output.mp3") -> bool:
    """
    Extracts audio from a local video file and saves as MP3 (16kHz, mono).
    """
    os.makedirs("temp_media", exist_ok=True)
    try:
        ffmpeg.input(video_path).output(
            output_filename,
            ar='16000',
            ac=1,
            **{'ab': '96k'},
            format='mp3',
            loglevel='error'
        ).run()
        return True
    except ffmpeg.Error as e:
        print(f"Error extracting audio: {e}")
        return False
