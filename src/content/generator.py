"""AETHER v7.8 — AI content generator (line-based format)"""
import json, re, requests
from datetime import datetime
from ..config import ROOT, OLLAMA_URL
from ..utils import setup_logger

log = setup_logger("content_gen")

OUTPUT_DIR = ROOT / "content_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

GEN_MODEL = "qwen3:1.7b"
TIMEOUT = 120

def _ask_model(prompt, model=GEN_MODEL, system=None, num_predict=600):
    payload = {"model": model, "prompt": prompt, "stream": False,
               "options": {"temperature": 0.7, "num_predict": num_predict}}
    if system:
        payload["system"] = system
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json().get("response", "").strip()
    except Exception as e:
        log.error(f"ollama: {e}")
    return ""

def _clean(text):
    """حيد markdown + thinking tags"""
    if not text:
        return ""
    # حيد  thinking... response ديال qwen3
    text = re.sub(r" thinking.*?", "", text, flags=re.DOTALL)
    text = re.sub(r"```[a-z]*\n?", "", text)
    text = text.replace("```", "")
    return text.strip()

def generate_meta(topic, language="ar"):
    """title + hook + thumbnail"""
    prompt = f"""الموضوع: {topic}

اكتب سطرين فقط:
TITLE: <عنوان جذاب 60 حرف>
HOOK: <جملة تجذب المشاهد>"""
    raw = _clean(_ask_model(prompt, num_predict=150))
    title = topic
    hook = f"مرحبا، اليوم كنشرحو {topic}"
    for line in raw.split("\n"):
        line = line.strip()
        if line.upper().startswith("TITLE:"):
            title = line[6:].strip()[:80]
        elif line.upper().startswith("HOOK:"):
            hook = line[5:].strip()[:200]
    return {"title": title, "hook": hook, "thumbnail_text": title[:30]}

def generate_body(topic, duration_min, language="ar"):
    """sections format: HEADING | content"""
    n_sections = max(2, min(4, duration_min // 2))
    prompt = f"""الموضوع: {topic}
اكتب {n_sections} أقسام لفيديو YouTube.

كل قسم = سطرين:
HEADING <رقم>: <عنوان القسم>
CONTENT <رقم>: <فقرة كاملة 3-4 جمل>

اكتب الأقسام {n_sections} فقط. بالدارجة المغربية."""
    raw = _clean(_ask_model(prompt, num_predict=800))
    sections = []
    current_head = None
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        up = line.upper()
        if up.startswith("HEADING"):
            head = re.sub(r"^HEADING\s*\d*\s*[:：\-]\s*", "", line, flags=re.IGNORECASE).strip()
            current_head = head
        elif up.startswith("CONTENT"):
            content = re.sub(r"^CONTENT\s*\d*\s*[:：\-]\s*", "", line, flags=re.IGNORECASE).strip()
            if current_head:
                sections.append({"heading": current_head, "content": content})
                current_head = None
    if not sections:
        # fallback: قسّم على السطور الفارغة
        blocks = [b.strip() for b in raw.split("\n\n") if b.strip()]
        for i, b in enumerate(blocks[:n_sections], 1):
            sections.append({"heading": f"القسم {i}", "content": b[:500]})
    if not sections:
        sections = [
            {"heading": "مقدمة", "content": f"اليوم غاديين نتكلمو على {topic}."},
            {"heading": "التفاصيل", "content": "..."},
        ]
    return {"sections": sections}

def generate_metadata(topic, language="ar"):
    prompt = f"""الموضوع: {topic}

اكتب:
TAGS: tag1, tag2, tag3, tag4, tag5
DESC: <وصف سطرين>"""
    raw = _clean(_ask_model(prompt, num_predict=300))
    tags = []
    desc = topic
    for line in raw.split("\n"):
        line = line.strip()
        up = line.upper()
        if up.startswith("TAGS:"):
            tags = [t.strip() for t in line[5:].split(",") if t.strip()][:8]
        elif up.startswith("DESC:"):
            desc = line[5:].strip()
    if not tags:
        tags = ["AI", "tools", "money", "2026"]
    return {"tags": tags, "description": desc}

def generate_script(topic, niche="ai_tools", duration_min=5, language="ar"):
    log.info(f"Generating: {topic} ({duration_min}min, {language})")

    meta = generate_meta(topic, language)
    log.info(f"✓ meta: {meta.get('title', '?')[:50]}")

    body = generate_body(topic, duration_min, language)
    log.info(f"✓ body: {len(body.get('sections', []))} sections")

    metadata = generate_metadata(topic, language)
    log.info(f"✓ metadata: {len(metadata.get('tags', []))} tags")

    data = {
        "title": meta.get("title", topic),
        "hook": meta.get("hook", ""),
        "thumbnail_text": meta.get("thumbnail_text", ""),
        "sections": body.get("sections", []),
        "tags": metadata.get("tags", []),
        "description": metadata.get("description", ""),
        "generated_at": datetime.now().isoformat(),
        "model": GEN_MODEL,
        "topic": topic,
    }

    safe_topic = re.sub(r"[^\w\-]", "_", topic)[:40]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = OUTPUT_DIR / f"script_{safe_topic}_{ts}.json"
    with open(out_file, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log.info(f"✓ saved: {out_file}")

    return {"file": str(out_file), "data": data}

def list_scripts():
    if not OUTPUT_DIR.exists():
        return []
    return sorted([str(p) for p in OUTPUT_DIR.glob("script_*.json")], reverse=True)

def format_script_text(data):
    out = []
    out.append(f"📺 {data.get('title', '?')}\n")
    out.append(f"🎣 {data.get('hook', '')}\n")
    for i, s in enumerate(data.get("sections", []), 1):
        out.append(f"\n━━━ {i}. {s.get('heading', '')} ━━━")
        out.append(s.get("content", "")[:600])
    out.append(f"\n🏷 Thumbnail: {data.get('thumbnail_text', '')}")
    out.append(f"🏷 Tags: {', '.join(data.get('tags', []))}")
    out.append(f"\n📄 {data.get('description', '')}")
    return "\n".join(out)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2 or sys.argv[1] == "list":
        for f in list_scripts():
            print(f)
    elif sys.argv[1] == "generate":
        topic = sys.argv[2] if len(sys.argv) > 2 else "5 AI tools"
        dur = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        lang = sys.argv[4] if len(sys.argv) > 4 else "ar"
        r = generate_script(topic, duration_min=dur, language=lang)
        print(f"✓ Saved: {r['file']}\n")
        print(format_script_text(r["data"]))
    elif sys.argv[1] == "show":
        path = sys.argv[2] if len(sys.argv) > 2 else (list_scripts() or [None])[0]
        if path:
            with open(path) as f:
                print(format_script_text(json.load(f)))
    else:
        print("Usage: {list|generate <topic> [min] [lang]|show [file]}")
