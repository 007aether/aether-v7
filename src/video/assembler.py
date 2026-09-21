"""AETHER v8.0 — Video assembler (ffmpeg)"""
import json, subprocess, shutil, os
from pathlib import Path
from ..config import ROOT
from ..utils import setup_logger
from .thumbnail import generate_thumbnail
from .voice import script_to_voice

log = setup_logger("assembler")

VIDEO_DIR = ROOT / "content_output" / "videos"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)

def _dur(path):
    """مدة ملف صوتي بالثواني"""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=10,
        )
        return float(r.stdout.strip() or 0)
    except Exception:
        return 0

def assemble(script_file, language="ar", fps=1):
    """يبني فيديو mp4 من script: thumbnail + voice"""
    if not shutil.which("ffmpeg"):
        return {"error": "ffmpeg not installed"}

    script_file = Path(script_file)
    with open(script_file) as f:
        data = json.load(f)

    # 1. voice
    log.info("Generating voice...")
    voice = script_to_voice(script_file, language)
    if not voice:
        return {"error": "voice generation failed"}

    # 2. thumbnail
    log.info("Generating thumbnail...")
    thumb = generate_thumbnail(script_file)
    if not thumb:
        return {"error": "thumbnail failed"}

    # 3. مدة الصوت
    duration = _dur(voice)
    if duration < 1:
        duration = 60
    log.info(f"Duration: {duration:.1f}s")

    # 4. اسم فيديو
    out_video = VIDEO_DIR / (script_file.stem + ".mp4")

    # 5. ffmpeg: صورة ثابتة + صوت = فيديو
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(thumb),
        "-i", str(voice),
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-t", str(duration + 1),
        str(out_video),
    ]
    log.info("Assembling video...")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            log.error(f"ffmpeg: {r.stderr[-500:]}")
            return {"error": "ffmpeg failed", "stderr": r.stderr[-500:]}
    except Exception as e:
        return {"error": str(e)}

    size_mb = out_video.stat().st_size / 1_048_576
    log.info(f"✓ video: {out_video} ({size_mb:.1f} MB)")

    return {
        "video": str(out_video),
        "thumbnail": thumb,
        "voice": voice,
        "duration": duration,
        "size_mb": round(size_mb, 2),
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        r = assemble(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "ar")
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        print("Usage: python -m src.video.assembler <script.json> [lang]")
