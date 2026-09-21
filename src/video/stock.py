"""AETHER v8.1 — Stock images (Pexels) + gradient fallback"""
import json, hashlib, requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from ..config import ROOT
from ..utils import setup_logger

log = setup_logger("stock")

IMG_DIR = ROOT / "content_output" / "images"
IMG_DIR.mkdir(parents=True, exist_ok=True)
PEXELS_KEY_FILE = ROOT / ".pexels_api_key"

W, H = 1920, 1080

def _get_key():
    try:
        return PEXELS_KEY_FILE.read_text().strip()
    except Exception:
        return None

def has_pexels():
    key = _get_key()
    return bool(key and len(key) > 10 and "YOUR_" not in key)

def fetch_pexels(query, n=5, orientation="landscape"):
    key = _get_key()
    if not key:
        return []
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "per_page": n, "orientation": orientation},
            headers={"Authorization": key},
            timeout=20,
        )
        if r.status_code != 200:
            log.error(f"pexels {r.status_code}: {r.text[:200]}")
            return []
        data = r.json()
        return [p["src"]["large"] for p in data.get("photos", [])]
    except Exception as e:
        log.error(f"pexels: {e}")
        return []

def download(url, prefix="img"):
    h = hashlib.md5(url.encode()).hexdigest()[:10]
    out = IMG_DIR / f"{prefix}_{h}.jpg"
    if out.exists():
        return str(out)
    try:
        r = requests.get(url, timeout=30, stream=True)
        if r.status_code == 200:
            with open(out, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            return str(out)
    except Exception as e:
        log.error(f"download: {e}")
    return None

def make_gradient(text_seed, out=None):
    h = int(hashlib.md5(text_seed.encode()).hexdigest()[:6], 16)
    c1 = (h & 0xFF, (h >> 8) & 0xFF, (h >> 16) & 0xFF)
    c2 = tuple(max(0, c - 80) for c in c1)

    img = Image.new("RGB", (W, H), c1)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        ratio = y / H
        r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
        g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
        b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    img = img.filter(ImageFilter.GaussianBlur(radius=8))

    out = Path(out or IMG_DIR / f"grad_{hashlib.md5(text_seed.encode()).hexdigest()[:8]}.jpg")
    img.save(out, "JPEG", quality=85)
    return str(out)

def _clean_query(q):
    """حيد الكلمات العربية إلا كان البحث إنجليزي أحسن"""
    if not q:
        return ""
    return q.strip()[:40]

def get_images_for_script(script_file, n=4):
    """جيب n صور (Pexels + fallback gradients)"""
    with open(script_file) as f:
        data = json.load(f)

    tags = [t for t in data.get("tags", []) if t and len(t) > 2]
    title = data.get("title", "")
    topic = data.get("topic", "")

    # queries: انجليزي أحسن
    queries = []
    # حاول نترجم الكلمات ديال الـ tags/title
    for q in tags + [title, topic]:
        q = _clean_query(q)
        if q and q not in queries:
            queries.append(q)

    images = []

    if has_pexels():
        for q in queries[:n*2]:  # جرب أكثر queries
            urls = fetch_pexels(q, n=1)
            if urls:
                p = download(urls[0], prefix=hashlib.md5(q.encode()).hexdigest()[:8])
                if p and p not in images:
                    images.append(p)
                    log.info(f"✓ {q}: {Path(p).name}")
            if len(images) >= n:
                break
        log.info(f"Pexels: {len(images)}/{n} images")

    # fallback gradients
    while len(images) < n:
        seed = f"{script_file}_{len(images)}"
        p = make_gradient(seed)
        images.append(p)

    return images[:n]

if __name__ == "__main__":
    import sys, json
    if len(sys.argv) > 1:
        r = get_images_for_script(sys.argv[1], n=4)
        print(json.dumps(r, indent=2))
    else:
        p = make_gradient("test")
        print(f"✓ {p}")
