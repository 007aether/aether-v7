"""AETHER v7 — Speech-to-text (whisper optional)"""
import shutil, subprocess, tempfile
from pathlib import Path
from ..utils import setup_logger

log = setup_logger("stt")

def has_whisper():
    return bool(shutil.which("whisper") or shutil.which("whisper-cli"))

def transcribe(audio_path):
    if not has_whisper():
        log.warning("whisper not installed")
        return None
    try:
        r = subprocess.run(
            ["whisper", str(audio_path), "--language", "ar",
             "--output_format", "txt", "--output_dir", "/tmp"],
            capture_output=True, text=True, timeout=300,
        )
        txt = Path("/tmp") / (Path(audio_path).stem + ".txt")
        if txt.exists():
            return txt.read_text().strip()
        return r.stdout.strip()
    except Exception as e:
        log.error(f"transcribe: {e}")
        return None

def record(seconds=5, output=None):
    if not shutil.which("arecord"):
        log.warning("arecord not installed")
        return None
    out = output or tempfile.mktemp(suffix=".wav")
    try:
        subprocess.run(
            ["arecord", "-d", str(seconds), "-f", "cd", "-t", "wav", out],
            timeout=seconds + 5, check=True,
        )
        return out
    except Exception as e:
        log.error(f"record: {e}")
        return None
