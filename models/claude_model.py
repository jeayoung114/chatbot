import os
import requests

def generate_response(prompt: str, *, api_key: str = None) -> str:
    api_key = api_key or os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        return "[Error] CLAUDE_API_KEY environment variable not set."
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    data = {
        "model": "claude-3-opus-20240229",  # or another Claude model
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.ok:
        content = response.json().get("content")
        if isinstance(content, list) and content and "text" in content[0]:
            return content[0]["text"]
        return "[No response from Claude]"
    return f"[Error from Claude API: {response.text}]" 