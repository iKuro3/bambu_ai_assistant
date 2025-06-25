import os
import json
import requests

class ChatAPIClient:
    """Simple wrapper for OpenAI's chat completion API with streaming."""

    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.endpoint = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")

    def send(self, user_message):
        """Send a user message and yield the streamed response chunks."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": user_message}],
            "stream": True,
        }
        with requests.post(self.endpoint, headers=headers, json=payload, stream=True) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                if line.startswith(b"data:"):
                    line = line[len(b"data:"):].strip()
                if line == b"[DONE]":
                    break
                data = json.loads(line.decode("utf-8"))
                delta = data.get("choices", [{}])[0].get("delta", {}).get("content")
                if delta:
                    yield delta
