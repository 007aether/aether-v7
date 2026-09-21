"""AETHER v8.1 — Video assembler v2 (multi-image + text overlays)"""
import json, subprocess, shutil, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from ..config import ROOT
from ..utils import setup_logger
from .thumbnail import generate_thumbnail, _font
from .voice import script_to_voice
from .stock import get_images_for_script

log = setup_logger("assembler")

VIDEO_DIR = ROOT / "content_output" / "videos"
TMP_DIR = ROOT / "content_output" / "tmp"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1920, 1080
ACCENT = (0, 255, 170)
WHITE = (255, 255, 255)

def _dur(path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=10,
        )
        return float(r.stdout.strip() or 0)
    except Exception:
        return 0

def _make_segment_image(bg_path, heading, content, out_path):
    try:
        bg = Image.open(bg_path).convert("RGB").resize((W, H))
    except Exception:
        bg = Image.new("RGB", (W, H), (10, 20, 40))

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 170))
    bg = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(bg)

    draw.rectangle([0, 0, W, 6], fill=ACCENT)

    f_head = _font(72, bold=True)
    f_body = _font(42)

    head_lines = textwrap.wrap(heading[:80], width=32)[:2]
    y = 140
    for line in head_lines:
        draw.text((80, y), line, font=f_head, fill=ACCENT)
        y += 90

    body_lines = textwrap.wrap(content[:400], width=55)[:8]
    y = 380
    for line in body_lines:
        draw.text((84, y + 3), line, font=f_body, fill=(0, 0, 0))
        draw.text((80, y), line, font=f_body, fill=WHITE)
        y += 58

    f_small = _font(24)
    draw.text((80, H - 60), "⚡ AETHER", font=f_small, fill=ACCENT)

    bg.save(out_path, "JPEG", quality=85)
    return out_path

def assemble(script_file, language="ar"):
    if not shutil.which("ffmpeg"):
        return {"error": "ffmpeg not installed"}

    script_file = Path(script_file)
    with open(script_file) as f:
        data = json.load(f)

    log.info("Generating voice...")
    voice = script_to_voice(script_file, language)
    if not voice:
        return {"error": "voice failed"}
    duration = _dur(voice) or 60
    log.info(f"Duration: {duration:.1f}s")

    log.info("Fetching images...")
    images = get_images_for_script(script_file, n=4)

    log.info("Building segments...")
    sections = data.get("sections", [])
    if not sections:
        sections = [{"heading": data.get("title", ""), "content": data.get("hook", "")}]

    n_seg = max(len(sections), 1)
    seg_dur = duration / n_seg

    segment_files = []
    for i, sec in enumerate(sections):
        bg = images[i % len(images)]
        seg_path = TMP_DIR / f"seg_{script_file.stem}_{i}.jpg"
        _make_segment_image(
            bg,
            sec.get("heading", f"القسم {i+1}"),
            sec.get("content", ""),
            seg_path,
        )
        segment_files.append(seg_path)

    concat_file = TMP_DIR / f"concat_{script_file.stem}.txt"
    with open(concat_file, "w") as f:
        for seg in segment_files:
            f.write(f"file '{seg}'\n")
            f.write(f"duration {seg_dur}\n")
        f.write(f"file '{segment_files[-1]}'\n")

    out_video = VIDEO_DIR / (script_file.stem + ".mp4")
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-i", str(voice),
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-r", "24",
        "-shortest",
        str(out_video),
    ]
    log.info("Assembling video...")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            log.error(f"ffmpeg: {r.stderr[-500:]}")
            return _assemble_static(script_file, voice, duration)
    except Exception as e:
        return {"error": str(e)}

    size_mb = out_video.stat().st_size / 1_048_576
    log.info(f"✓ video v2: {out_video} ({size_mb:.1f} MB)")

    return {
        "video": str(out_video),
        "voice": voice,
        "duration": round(duration, 1),
        "size_mb": round(size_mb, 2),
        "segments": n_seg,
        "images_used": len(images),
    }

def _assemble_static(script_file, voice, duration):
    log.warning("Fallback: static")
    thumb = generate_thumbnail(str(script_file))
    out_video = VIDEO_DIR / (Path(script_file).stem + ".mp4")
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(thumb),
        "-i", str(voice),
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest", str(out_video),
    ]
    subprocess.run(cmd, capture_output=True, timeout=300)
    return {"video": str(out_video), "voice": voice,
            "duration": duration, "mode": "static_fallback"}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        r = assemble(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "ar")
        print(json.dumps(r, indent=2, ensure_ascii=False))
