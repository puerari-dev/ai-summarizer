from openai import OpenAI
from config import OPENAI_API_KEY
from config import GPT4_INPUT_COST_PER_K, GPT4_OUTPUT_COST_PER_K

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_summary(transcript: str) -> str:
    """
    Generates a Markdown summary from the transcript using GPT-4o.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert in summarizing video transcripts. "
                "Read the provided transcript and produce a concise summary capturing the main ideas, key points, and conclusion. "
                "Use Markdown formatting for headers, bullet lists, and emphasis. "
                "The transcript can be in Portuguese (Brazilian) or English. Ensure the summary is in the same language as the transcript."
            )
        },
        {
            "role": "user",
            "content": transcript
        }
    ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0
    )

    # Calculate cost
    input_cost = (response.usage.prompt_tokens / 1000) * GPT4_INPUT_COST_PER_K
    output_cost = (response.usage.completion_tokens / 1000) * GPT4_OUTPUT_COST_PER_K
    total_cost = input_cost + output_cost
    
    return response.choices[0].message.content, total_cost
