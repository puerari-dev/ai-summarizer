import ffmpeg
import math
import os
from utils import get_audio_duration

def partition_audio_equal(audio_path: str, num_chunks: int) -> list:
    """
    Partitions the audio file into num_chunks equal parts.
    Returns a list of chunk file names.
    """
    os.makedirs("temp_media", exist_ok=True)
    total_duration = get_audio_duration(audio_path)
    if total_duration == 0:
        return []
    chunk_duration = total_duration / num_chunks
    chunks = []
    for i in range(num_chunks):
        start = i * chunk_duration
        # For the last chunk, ensure we cover the remaining audio
        duration = chunk_duration if (i != num_chunks - 1) else (total_duration - start)
        chunk_filename = os.path.join("temp_media", f"chunk_equal_{i}.mp3")
        try:
            (
                ffmpeg.input(audio_path, ss=start, t=duration)
                .output(chunk_filename, ar='16000', ac=1, format='mp3', **{'audio_bitrate': '96k'}, loglevel='error')
                .run()
            )
            chunks.append(chunk_filename)
        except ffmpeg.Error as e:
            print(f"Error creating chunk {i}: {e}")
    return chunks

def partition_audio_by_timestamps(audio_path: str, timestamps: list) -> list:
    """
    Partitions the audio file based on provided timestamps.
    `timestamps` should be a list of tuples (start_time_in_seconds, label).
    Returns a list of tuples (chunk_filename, label).
    """
    os.makedirs("temp_media", exist_ok=True)
    total_duration = get_audio_duration(audio_path)
    chunks = []
    for i, (start, label) in enumerate(timestamps):
        # Determine the end time: next timestamp or total duration
        end = timestamps[i+1][0] if i+1 < len(timestamps) else total_duration
        duration = end - start
        chunk_filename = os.path.join("temp_media", f"chunk_{i}_{label}.mp3")
        try:
            (
                ffmpeg.input(audio_path, ss=start, t=duration)
                .output(chunk_filename, ar='16000', ac=1, format='mp3', **{'audio_bitrate': '96k'}, loglevel='error')
                .run()
            )
            chunks.append((chunk_filename, label))
        except ffmpeg.Error as e:
            print(f"Error creating chunk for {label}: {e}")
    return chunks
