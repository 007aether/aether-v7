"""AETHER v8.0 — Thumbnail generator (Pillow)"""
import json, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from ..config import ROOT
from ..utils import setup_logger

log = setup_logger("thumbnail")

THUMB_DIR = ROOT / "content_output" / "thumbnails"
THUMB_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1280, 720
BG = (10, 20, 40)
ACCENT = (0, 255, 170)
WHITE = (255, 255, 255)

def _font(size, bold=False):
    """يلقى خط عربي/إنجليزي"""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()

def generate_thumbnail(script_file, output_path=None):
    """يولد thumbnail من script"""
    with open(script_file) as f:
        data = json.load(f)

    title = data.get("title", "AETHER")[:60]
    text = data.get("thumbnail_text") or title

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # gradient بسيط
    for y in range(H):
        ratio = y / H
        r = int(BG[0] + (0 - BG[0]) * ratio * 0.5)
        g = int(BG[1] + (30 - BG[1]) * ratio * 0.5)
        b = int(BG[2] + (60 - BG[2]) * ratio * 0.5)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # شريط أعلى
    draw.rectangle([0, 0, W, 8], fill=ACCENT)
    draw.rectangle([0, H - 8, W, H], fill=ACCENT)

    # نص العنوان (وسط)
    font_big = _font(80, bold=True)
    font_small = _font(32)

    lines = textwrap.wrap(text, width=25)
    if len(lines) > 3:
        lines = lines[:3]

    total_h = sum(font_big.getbbox(l)[3] + 20 for l in lines)
    y = (H - total_h) // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_big)
        w = bbox[2] - bbox[0]
        x = (W - w) // 2
        # shadow
        draw.text((x + 4, y + 4), line, font=font_big, fill=(0, 0, 0))
        # accent
        draw.text((x, y), line, font=font_big, fill=ACCENT)
        y += font_big.getbbox(line)[3] + 20

    # أسفل: علامة AETHER
    label = "⚡ AETHER"
    draw.text((40, H - 70), label, font=font_small, fill=ACCENT)
    right_label = "v8.0"
    bbox = draw.textbbox((0, 0), right_label, font=font_small)
    draw.text((W - bbox[2] - 40, H - 70), right_label, font=font_small, fill=ACCENT)

    # احفظ
    out = Path(output_path or (THUMB_DIR / (Path(script_file).stem + ".jpg")))
    img.save(out, "JPEG", quality=88)
    log.info(f"✓ thumbnail: {out}")
    return str(out)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        r = generate_thumbnail(sys.argv[1])
        print(json.dumps({"thumbnail": r}, indent=2))
    else:
        print("Usage: python -m src.video.thumbnail <script.json>")
