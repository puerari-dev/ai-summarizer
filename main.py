import argparse
import os
from audio_extractor import download_youtube_audio, extract_audio_from_video
from audio_chunker import partition_audio_equal, partition_audio_by_timestamps
from transcription import transcribe_audio
from summarization import generate_summary
from youtube_processor import get_video_description, extract_timestamps_from_description
from utils import save_markdown, clean_filename, get_audio_duration

# Set a threshold duration in seconds for "short" videos (e.g., 10 minutes)
SHORT_DURATION_THRESHOLD = 30 * 60  # 30 minutes

def process_short_audio(audio_path: str, output_prefix: str):
    """
    Processes short audio files: transcribes the whole audio, generates a summary, and saves the results.
    """
    print("Processing short audio file...")
    
    transcript, transcript_cost = transcribe_audio(audio_path)
    summary, summary_cost = generate_summary(transcript)
    
    save_markdown(f"{output_prefix}_transcript.md", transcript)
    save_markdown(f"{output_prefix}_summary.md", summary)
    
    print("\nCosts:")
    print(f"• Transcription: ${transcript_cost:.4f}")
    print(f"• Summary: ${summary_cost:.4f}")
    print(f"• Total: ${transcript_cost + summary_cost:.4f}\n")
    print("Transcription and summary saved.")

def process_long_audio_equal(audio_path: str, output_prefix: str, num_chunks: int = 4):
    """
    Processes long audio files by equal partitioning.
    Transcribes and summarizes each chunk, then merges the results.
    """
    print("Processing long audio file with equal partitioning...")
    total_transcript_cost = 0.0
    total_summary_cost = 0.0

    chunk_files = partition_audio_equal(audio_path, num_chunks)
    chunk_transcripts = []
    chunk_summaries = []

    for i, chunk in enumerate(chunk_files):
        print(f"Transcribing chunk {i}...")
        transcript, chunk_trans_cost = transcribe_audio(chunk)
        total_transcript_cost += chunk_trans_cost
        chunk_transcripts.append(transcript)
        save_markdown(f"{output_prefix}_chunk_{i}_transcript.md", transcript)

        print(f"Summarizing chunk {i}...")
        summary, chunk_sum_cost = generate_summary(transcript)
        total_summary_cost += chunk_sum_cost
        chunk_summaries.append(summary)
        save_markdown(f"{output_prefix}_chunk_{i}_summary.md", summary)

        os.remove(chunk)

    merged_transcript = "\n\n".join(chunk_transcripts)
    merged_summary = "\n\n".join(chunk_summaries)
    final_summary, final_sum_cost = generate_summary(merged_summary)
    total_summary_cost += final_sum_cost

    save_markdown(f"{output_prefix}_merged_transcript.md", merged_transcript)
    save_markdown(f"{output_prefix}_merged_summary.md", merged_summary)
    save_markdown(f"{output_prefix}_final_summary.md", final_summary)

    print("\nCosts:")
    print(f"• Transcription: ${total_transcript_cost:.4f}")
    print(f"• Summary: ${total_summary_cost:.4f}")
    print(f"• Total: ${total_transcript_cost + total_summary_cost:.4f}\n")
    print("Merged transcription and summaries saved.")

def process_long_audio_timestamps(audio_path: str, output_prefix: str, description: str):
    """
    Processes long audio files using timestamp-based partitioning (used for YouTube videos).
    Extracts timestamps from the description, partitions the audio accordingly, then transcribes and summarizes each section.
    """
    print("Processing long audio file with timestamp partitioning...")
    total_transcript_cost = 0.0
    total_summary_cost = 0.0

    timestamps = extract_timestamps_from_description(description)
    if not timestamps:
        print("No timestamps found in description. Falling back to equal partitioning.")
        process_long_audio_equal(audio_path, output_prefix)
        return
    chunk_info = partition_audio_by_timestamps(audio_path, timestamps)
    section_transcripts = []
    section_summaries = []

    for i, (chunk_file, label) in enumerate(chunk_info):
        print(f"Transcribing section {label}...")
        transcript, chunk_trans_cost = transcribe_audio(chunk_file)
        total_transcript_cost += chunk_trans_cost
        section_transcripts.append(f"## {label}\n\n{transcript}")
        save_markdown(f"{output_prefix}_{label}_transcript.md", transcript)

        print(f"Summarizing section {label}...")
        summary, chunk_sum_cost = generate_summary(transcript)
        total_summary_cost += chunk_sum_cost
        section_summaries.append(f"## {label}\n\n{summary}")
        save_markdown(f"{output_prefix}_{label}_summary.md", summary)
        
        os.remove(chunk_file)

    merged_transcript = "\n\n".join(section_transcripts)
    merged_summary = "\n\n".join(section_summaries)
    final_summary, final_sum_cost = generate_summary(merged_summary)
    total_summary_cost += final_sum_cost

    save_markdown(f"{output_prefix}_merged_transcript.md", merged_transcript)
    save_markdown(f"{output_prefix}_merged_summary.md", merged_summary)
    save_markdown(f"{output_prefix}_final_summary.md", final_summary)

    print("\nCosts:")
    print(f"• Transcription: ${total_transcript_cost:.4f}")
    print(f"• Summary: ${total_summary_cost:.4f}")
    print(f"• Total: ${total_transcript_cost + total_summary_cost:.4f}\n")
    print("Merged transcription and summaries saved.")

def main():
    parser = argparse.ArgumentParser(description="AI Video Summarizer")
    parser.add_argument("--input", required=True, help="YouTube URL or local video file path")
    parser.add_argument("--partition", choices=["equal", "timestamps"], help="Partitioning method for long videos. (timestamps only works for YouTube if timestamps exist)")
    args = parser.parse_args()

    input_source = args.input

    temp_media_dir = "temp_media"
    os.makedirs(temp_media_dir, exist_ok=True)
    audio_file = os.path.join(temp_media_dir, "output.mp3")

    output_dir = "transcription_and_summaries"
    os.makedirs(output_dir, exist_ok=True)

    if input_source.startswith("http"):
        print("Processing YouTube URL...")
        success, video_title = download_youtube_audio(input_source, audio_file)
        if not success:
            print("Failed to download YouTube audio.")
            return
        description = get_video_description(input_source)
        base_name = clean_filename(video_title)
    else:
        print("Processing local video file...")
        if not extract_audio_from_video(input_source, audio_file):
            print("Failed to extract audio from local video.")
            return
        description = ""
        base_name = os.path.splitext(os.path.basename(input_source))[0]
        base_name = clean_filename(base_name)

    output_prefix = os.path.join(output_dir, base_name)

    duration = get_audio_duration(audio_file)
    print(f"Audio duration: {duration:.2f} seconds.")

    if duration <= SHORT_DURATION_THRESHOLD:
        process_short_audio(audio_file, output_prefix)
    else:
        if input_source.startswith("http") and args.partition == "timestamps":
            process_long_audio_timestamps(audio_file, output_prefix, description)
        else:
            process_long_audio_equal(audio_file, output_prefix)

    if os.path.exists(audio_file):
        os.remove(audio_file)
    print("Processing complete.")

if __name__ == "__main__":
    main()
