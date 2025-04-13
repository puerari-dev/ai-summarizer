from openai import OpenAI
from config import OPENAI_API_KEY
from utils import get_audio_duration
from config import WHISPER_COST_PER_MINUTE

client = OpenAI(api_key=OPENAI_API_KEY)

def transcribe_audio(audio_file: str) -> tuple[str, float]:
    """
    Returns transcription text and processing cost
    """
    duration = get_audio_duration(audio_file)
    
    with open(audio_file, "rb") as file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=file
        )
    
    # Calculate cost
    minutes = duration / 60
    cost = minutes * WHISPER_COST_PER_MINUTE
    
    return transcription.text, cost