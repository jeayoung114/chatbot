import requests

def generate_response(prompt: str) -> str:
    # Replace with your actual Hugging Face endpoint and token
    API_URL = "https://api-inference.huggingface.co/models/your-model"
    headers = {"Authorization": f"Bearer YOUR_HF_TOKEN"}
    payload = {"inputs": prompt}
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.ok:
        return response.json()[0]["generated_text"]
    return "[Error from Hugging Face API]" 