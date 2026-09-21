"""AETHER v9 — Warmup models (keep in RAM)"""
import requests, time
from .config import OLLAMA_URL
from .utils import setup_logger

log = setup_logger("warmup")

MODELS = ["qwen3:1.7b", "hermes3:latest"]

def warmup(model, timeout=120):
    """طلب صغير باش الموديل يبقى فـ RAM"""
    try:
        t0 = time.time()
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": "/no_think\nhi",
                "stream": False,
                "keep_alive": "2h",
                "options": {"num_predict": 5, "num_ctx": 512},
            },
            timeout=timeout,
        )
        dt = time.time() - t0
        if r.status_code == 200:
            log.info(f"✓ {model} warm ({dt:.1f}s)")
            return True
    except Exception as e:
        log.error(f"{model}: {e}")
    return False

def warmup_all():
    for m in MODELS:
        warmup(m, timeout=180)

if __name__ == "__main__":
    warmup_all()
