import openai
import os

def generate_response(prompt: str, *, api_key: str = None) -> str:
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "[Error] OPENAI_API_KEY environment variable not set."
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content 