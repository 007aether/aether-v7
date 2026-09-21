"""AETHER v7 — Central Config"""
import os
from pathlib import Path

ROOT = Path("/home/aether/AETHER_Project")
V7   = ROOT / "aether-v7"
DATA = V7 / "data"
LOGS = DATA / "logs"

DB_PATH      = DATA / "aether.db"
EARNINGS_DB  = DATA / "earnings.db"

VENV_PYTHON  = ROOT / ".venv" / "bin" / "python3"

OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "hermes3:latest"

TOKEN_FILE   = ROOT / ".bot_token"
ADMIN_FILE   = ROOT / ".telegram_chat_id"

DASHBOARD_PORT = 9092

# Old DBs (for migration only)
OLD_MEM_DB = ROOT / "aether_memory.db"
OLD_EAR_DB = ROOT / "earnings.db"

for d in (DATA, LOGS):
    d.mkdir(parents=True, exist_ok=True)
