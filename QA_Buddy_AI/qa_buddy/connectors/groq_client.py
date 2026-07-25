"""GROQ API client — OpenAI-compatible, streaming support."""

from openai import OpenAI
from qa_buddy.config import config


class GroqClient:
    def __init__(self):
        self._client = None

    def _ensure(self):
        if self._client is not None:
            return
        self._client = OpenAI(
            api_key=config.GROQ_API_KEY,
            base_url=config.GROQ_BASE_URL,
        )

    def stream(self, messages: list[dict]):
        self._ensure()
        response = self._client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=4096,
            stream=True,
        )
        for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content

    def complete(self, messages: list[dict]) -> str:
        self._ensure()
        response = self._client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=4096,
        )
        return response.choices[0].message.content
