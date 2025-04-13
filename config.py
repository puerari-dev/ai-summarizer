import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Please set the OPENAI_API_KEY in your .env file.")

WHISPER_COST_PER_MINUTE = 0.006  # $0.006/min
GPT4_INPUT_COST_PER_K = 0.005    # $0.005/1k tokens input
GPT4_OUTPUT_COST_PER_K = 0.015   # $0.015/1k tokens output