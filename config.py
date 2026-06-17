# 기본값 설정

import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")

QUEUE_MAX_SIZE = 10
HISTORY_SCAN_LIMIT = 50
HISTORY_USE_LIMIT = 10