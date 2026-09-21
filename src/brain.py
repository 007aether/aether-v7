"""AETHER v9 — Fast brain with /no_think + keep_alive"""
import re, requests
from .config import OLLAMA_URL, OLLAMA_MODEL
from .cache import cached
from .utils import setup_logger

log = setup_logger("brain")

FAST_MODEL = "qwen3:1.7b"
DEEP_MODEL = OLLAMA_MODEL  # hermes3:latest
NO_THINK = "/no_think"

def _post(model, prompt, system=None, num_predict=250, timeout=90):
    """استدعاء ollama مع keep_alive + خيارات محسّنة"""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "30m",       # يخلي الموديل فـ RAM
        "options": {
            "num_predict": num_predict,
            "temperature": 0.6,
            "top_p": 0.9,
            "num_ctx": 2048,       # context أصغر = أسرع
        },
    }
    if system:
        payload["system"] = system
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        if r.status_code == 200:
            txt = r.json().get("response", "").strip()
            # حيد thinking blocks
            txt = re.sub(r" thinking.*? response", "", txt, flags=re.DOTALL)
            txt = re.sub(r"^(Thinking|Hmm|Let me).*?\n\n", "", txt, flags=re.DOTALL)
            return txt.strip()
    except Exception as e:
        log.error(f"ollama {model}: {e}")
    return ""

@cached(ttl=60)
def ask(prompt, system=None):
    """سريع: qwen3 + /no_think"""
    sys = system or "أنت ESPRIEAETHER، عقل رقمي مغربي مختصر ومباشر."
    full = f"{NO_THINK}\n{prompt}"
    return _post(FAST_MODEL, full, sys, num_predict=250, timeout=60)

@cached(ttl=120)
def ask_deep(prompt, system=None):
    """ذكي: hermes3 للأسئلة المعقدة"""
    sys = system or "أنت ESPRIEAETHER، عقل رقمي مغربي."
    return _post(DEEP_MODEL, prompt, sys, num_predict=400, timeout=180)

def log_event(level, source, message):
    from .db import connect_memory
    from .utils import now
    c = connect_memory()
    c.execute("INSERT INTO events (ts,level,source,message) VALUES (?,?,?,?)",
              (now(), level, source, message))
    c.commit(); c.close()

def log_cycle(obs, decision, action="cycle", success=True):
    from .db import connect_memory
    from .utils import now
    c = connect_memory()
    c.execute("INSERT INTO cycles (ts,observation,decision,action,success) VALUES (?,?,?,?,?)",
              (now(), obs, decision, action, 1 if success else 0))
    c.commit(); c.close()

def think(obs):
    d = ask(f"{obs}\n\nقرار قصير بالدارجة (سطر واحد):") or "لا قرار"
    log_cycle(obs, d)
    log.info(f"Decision: {d[:80]}")
    return d

def remember(key, value, category="general"):
    from .db import connect_memory
    from .utils import now
    c = connect_memory()
    c.execute("""INSERT INTO memory (key,value,category,ts) VALUES (?,?,?,?)
                 ON CONFLICT(key) DO UPDATE SET value=excluded.value, ts=excluded.ts""",
              (key, value, category, now()))
    c.commit(); c.close()

def recall(key):
    from .db import connect_memory
    c = connect_memory()
    r = c.execute("SELECT value FROM memory WHERE key=?", (key,)).fetchone()
    c.close()
    return r[0] if r else None
