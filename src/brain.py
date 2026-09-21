"""AETHER v7 — AI Brain"""
import requests
from .config import OLLAMA_URL, OLLAMA_MODEL
from .db import connect_memory
from .utils import now, setup_logger

log = setup_logger("brain")

def ask(prompt, system="أنت AETHER، عقل رقمي مغربي. تفهم الدارجة والعربية وتتخذ قرارات صيانة محلياً."):
    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "system": system,
                  "prompt": prompt, "stream": False},
            timeout=180,
        )
        if r.status_code == 200:
            return r.json().get("response", "").strip()
    except Exception as e:
        log.error(f"ollama: {e}")
    return ""

def log_event(level, source, message):
    c = connect_memory()
    c.execute("INSERT INTO events (ts,level,source,message) VALUES (?,?,?,?)",
              (now(), level, source, message))
    c.commit(); c.close()

def log_cycle(obs, decision, action="cycle", success=True):
    c = connect_memory()
    c.execute("INSERT INTO cycles (ts,observation,decision,action,success) VALUES (?,?,?,?,?)",
              (now(), obs, decision, action, 1 if success else 0))
    c.commit(); c.close()

def think(obs):
    prompt = f"{obs}\n\nعطني قرار قصير جداً بالدارجة (سطر واحد فقط)."
    d = ask(prompt) or "لا قرار"
    log_cycle(obs, d)
    log.info(f"Decision: {d[:80]}")
    return d

def remember(key, value, category="general"):
    c = connect_memory()
    c.execute("""INSERT INTO memory (key,value,category,ts) VALUES (?,?,?,?)
                 ON CONFLICT(key) DO UPDATE SET value=excluded.value, ts=excluded.ts""",
              (key, value, category, now()))
    c.commit(); c.close()

def recall(key):
    c = connect_memory()
    r = c.execute("SELECT value FROM memory WHERE key=?", (key,)).fetchone()
    c.close()
    return r[0] if r else None
