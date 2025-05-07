# AI Video Summarizer

This project provides an automated workflow to:
1. **Download or extract audio** from a YouTube link or local video file.
2. **Transcribe** the audio using OpenAI's Whisper model.
3. **Summarize** the transcribed text using GPT-4.
4. **Save** the transcription and summary as Markdown files.

Now featuring a user-friendly web interface built with Streamlit!

It supports:
- Equal partitioning of the audio for large files.
- Timestamp-based partitioning using timestamps found in the YouTube video description (if available).
- Automatic cost estimation for both Whisper (transcription) and GPT-4 (summary).

## Table of Contents
- [Features](#features)
- [Prerequisites and Installation](#prerequisites-and-installation)
- [Environment Variables](#environment-variables)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Cost Calculation](#cost-calculation)
- [Notes](#notes)
- [License](#license)

---

## Features
- **Short Videos**: If the video/audio is under a certain duration threshold (default: 30 minutes), it will be fully transcribed and summarized in one shot.
- **Long Videos**:
  - **Equal Partitioning**: Splits the audio into multiple equal chunks, transcribes and summarizes each, then merges the outputs.
  - **Timestamp Partitioning**: For YouTube videos, you can provide `--partition timestamps` to parse the video's description for timestamps and create chunks accordingly, allowing fine-grained, chapter-based summarization.
- **Cost Estimation**: Automatically calculates the approximate usage cost for Whisper and GPT-4.

---

## Prerequisites and Installation

1. **Python Version**  
   Requires **Python 3.8+**.

2. **Install Dependencies**  
   Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```
   Or install them manually (below is a general example; your versions may vary):
   ```bash
   pip install openai python-dotenv yt-dlp ffmpeg-python streamlit
   ```
   - `openai` – to access GPT-4 and Whisper.
   - `python-dotenv` – to load environment variables from a `.env` file.
   - `yt-dlp` – to download audio from YouTube.
   - `ffmpeg-python` – to handle audio processing (requires FFmpeg installed on your system).
   - `streamlit` – to provide the web interface.

3. **Install FFmpeg**  
   Ensure that [FFmpeg](https://ffmpeg.org/) is installed and accessible via your system’s PATH.  
   - On macOS (with Homebrew): `brew install ffmpeg`  
   - On Ubuntu/Debian: `sudo apt-get update && sudo apt-get install ffmpeg`  
   - On Windows: Download from the official website and add it to your PATH.

---

## Environment Variables

Create a `.env` file in the project root with the following content:

```bash
OPENAI_API_KEY=<Your_OpenAI_API_Key>
```

This key is used for both Whisper (audio transcription) and GPT-4 (summaries).  
If `OPENAI_API_KEY` is not set, the script will raise an error.

Additionally, you can customize cost constants in `config.py` (though default values are provided):
```python
WHISPER_COST_PER_MINUTE = 0.006    # $0.006 per minute (default)
GPT4_INPUT_COST_PER_K    = 0.005   # $0.005 per 1000 tokens of input (default)
GPT4_OUTPUT_COST_PER_K   = 0.015   # $0.015 per 1000 tokens of output (default)
```

---

## Usage

You can use this tool in two ways:

### 1. Web Interface (Recommended)
Run the Streamlit interface for a user-friendly experience:

```bash
streamlit run app.py
```

This will open a web interface where you can:
- Paste a YouTube URL or upload a local video file
- Choose the partitioning method (equal or timestamps)
- View real-time progress
- See cost estimates
- Access the generated transcriptions and summaries

### 2. Command Line Interface
Run the main script with the following arguments:

```bash
python main.py --input <SOURCE> [--partition <METHOD>]
```

### Arguments

- `--input <SOURCE>`  
  - **YouTube URL** (e.g., `https://www.youtube.com/watch?v=<VIDEO_ID>`)  
  - **Local video file** path (e.g., `path/to/video.mp4`).

- `--partition <METHOD>`  
  - **`equal`** – Splits the audio into four equal chunks if the video is considered “long” (default threshold: 30 minutes).  
  - **`timestamps`** – Uses timestamps from the YouTube description. Only valid for YouTube links if timestamps are present in the description.

### Examples

1. **Short Local Video**  
   If your local video is less than ~30 minutes, it will be processed in one shot:
   ```bash
   python main.py --input "my_short_video.mp4"
   ```

2. **Long YouTube Video with Equal Partitioning**  
   ```bash
   python main.py --input "https://youtube.com/watch?v=abc123" --partition equal
   ```

3. **Long YouTube Video with Timestamp Partitioning**  
   ```bash
   python main.py --input "https://youtube.com/watch?v=abc123" --partition timestamps
   ```
   - If timestamps are found in the YouTube description, each chunk is processed separately.
   - If no timestamps are found, it falls back to equal partitioning.

---

## Project Structure

```plaintext
.
├─ app.py                   # Streamlit web interface
├─ audio_chunker.py         # Splits audio files into chunks (equal or timestamp-based)
├─ audio_extractor.py       # Downloads YouTube audio or extracts audio from local video
├─ config.py                # Environment variables and cost configurations
├─ main.py                  # CLI entry point, orchestrates the entire process
├─ summarization.py         # Summarizes text using GPT-4
├─ transcription.py         # Transcribes audio using Whisper
├─ utils.py                 # Helper functions (clean filenames, save Markdown, etc.)
├─ youtube_processor.py     # Fetches YouTube metadata (description, timestamps)
├─ requirements.txt         # Python dependencies
└─ README.md                # Documentation (this file)
```

**Key Directories (auto-created):**
- **`temp_media/`** – Temporary working directory for downloaded or extracted audio and chunked segments.
- **`transcription_and_summaries/`** – Final output location for transcripts and summaries in Markdown format.

---

## How It Works

1. **Audio Acquisition**  
   - If the input is a YouTube URL, `audio_extractor.py` downloads the audio track using `yt-dlp`.  
   - If the input is a local video file, `audio_extractor.py` extracts its audio with FFmpeg.

2. **Determining Video Length**  
   - Using `ffmpeg-python`, the script checks the total audio duration.
   - If the audio is under `SHORT_DURATION_THRESHOLD` (default: 30 minutes), a single-step transcription and summary is performed.
   - Otherwise, the script either partitions the audio into equal chunks or uses timestamps found in the YouTube description (if requested).

3. **Transcription**  
   - Each audio segment is transcribed via `transcription.py`, which calls `OpenAI`’s Whisper model.
   - A cost estimate is computed based on the total transcription length (minutes × `WHISPER_COST_PER_MINUTE`).

4. **Summarization**  
   - `summarization.py` sends the transcription to GPT-4 for summarization.
   - A cost estimate is computed by multiplying input/output token counts by `GPT4_INPUT_COST_PER_K` / `GPT4_OUTPUT_COST_PER_K`.

5. **Output**  
   - Each chunk’s transcript and summary is saved to Markdown (`_transcript.md`, `_summary.md`).
   - If multiple chunks exist, a merged transcript and merged summary are also generated, plus a final summary of the merged summary.

---

## Notes

- **File Clean-Up**: Temporary chunk files are removed at the end of processing.  
- **Timestamps**: The format for timestamps in a YouTube description must be `HH:MM:SS Section Title` or `MM:SS Section Title`. This is parsed by `youtube_processor.py`.
- **Error Handling**: If something fails (e.g., audio extraction), the script will print an error message and terminate.
- **International Languages**: The entire pipeline works with English, Portuguese (Brazilian), and should handle other languages recognized by Whisper/GPT-4.

---

## License

This project is provided as-is. Check [OpenAI’s terms](https://openai.com/policies/) for usage of their APIs, and review the licenses of any libraries used (e.g., [FFmpeg](https://ffmpeg.org/legal.html), [yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE), etc.).

Enjoy summarizing your videos automatically!
