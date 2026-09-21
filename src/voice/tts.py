"""AETHER v7 — Text-to-speech (espeak-ng)"""
import subprocess, shutil
from ..utils import setup_logger

log = setup_logger("tts")

def has_tts():
    return bool(shutil.which("espeak-ng") or shutil.which("espeak"))

def speak(text, lang="ar"):
    if not has_tts():
        log.warning("No TTS engine (install: sudo apt install espeak-ng)")
        return False
    cmd = "espeak-ng" if shutil.which("espeak-ng") else "espeak"
    try:
        subprocess.run([cmd, "-v", lang, text], timeout=60, check=False)
        return True
    except Exception as e:
        log.error(f"speak: {e}")
        return False

def test():
    return speak("مرحبا، أنا أيثر، النظام خدام")
