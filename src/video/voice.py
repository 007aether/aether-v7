"""AETHER v8.0 — Voice generation (edge-tts)"""
import asyncio, subprocess, shutil
from pathlib import Path
from ..config import ROOT
from ..utils import setup_logger

log = setup_logger("voice")

AUDIO_DIR = ROOT / "content_output" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# أصوات عربية وإنجليزية من edge-tts
VOICES = {
    "ar": "ar-EG-ShakirNeural",       # صوت عربي
    "ar-ma": "ar-MA-JamalNeural",     # دارجة مغربية
    "en": "en-US-ChristopherNeural",  # إنجليزي
    "fr": "fr-FR-HenriNeural",
}

def generate_voice_edge(text, output_path=None, language="ar"):
    """يولد صوت بـ edge-tts (online، مجاني)"""
    try:
        import edge_tts
    except ImportError:
        log.error("edge-tts not installed")
        return None

    voice = VOICES.get(language, VOICES["ar"])
    out = Path(output_path or AUDIO_DIR / f"voice_{abs(hash(text)) % 100000}.mp3")

    async def _run():
        comm = edge_tts.Communicate(text, voice)
        await comm.save(str(out))

    try:
        asyncio.run(_run())
        log.info(f"✓ voice: {out} ({out.stat().st_size} bytes)")
        return str(out)
    except Exception as e:
        log.error(f"edge-tts: {e}")
        return None

def generate_voice_espeak(text, output_path=None, language="ar"):
    """fallback: espeak-ng (offline)"""
    if not shutil.which("espeak-ng"):
        return None
    out = Path(output_path or AUDIO_DIR / f"voice_esp_{abs(hash(text)) % 100000}.wav")
    try:
        subprocess.run(
            ["espeak-ng", "-v", language, "-s", "140", "-w", str(out), text],
            check=True, timeout=60,
        )
        return str(out)
    except Exception as e:
        log.error(f"espeak: {e}")
        return None

def generate(text, output_path=None, language="ar"):
    """يحاول edge-tts، ومن بعد espeak"""
    r = generate_voice_edge(text, output_path, language)
    if r:
        return r
    log.warning("edge-tts failed, trying espeak")
    return generate_voice_espeak(text, output_path, language)

def script_to_voice(script_file, language="ar"):
    """يولد صوت كامل من script"""
    import json
    with open(script_file) as f:
        data = json.load(f)

    # جمع النص
    parts = []
    if data.get("hook"):
        parts.append(data["hook"])
    for s in data.get("sections", []):
        parts.append(s.get("content", ""))
    full_text = "\n\n".join(parts)

    # اسم ملف من script
    base = Path(script_file).stem
    out = AUDIO_DIR / f"{base}.mp3"
    return generate(full_text, out, language)


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) > 1:
        r = script_to_voice(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "ar")
        print(json.dumps({"voice": r}, indent=2))
    else:
        # test
        r = generate("مرحبا، أنا أيثر، هذا اختبار الصوت", None, "ar")
        print(f"Voice: {r}")
