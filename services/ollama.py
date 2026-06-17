import aiohttp
from config import OLLAMA_MODEL, OLLAMA_URL


async def ask_ollama(messages: list[dict]) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.3
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(OLLAMA_URL, json=payload, timeout=120) as response:
            response.raise_for_status()
            data = await response.json()
            return data["message"]["content"]