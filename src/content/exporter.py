"""AETHER v7.9 — Script exporters"""
import json, re
from pathlib import Path
from ..config import ROOT
from ..utils import setup_logger

log = setup_logger("exporter")
OUTPUT_DIR = ROOT / "content_output"

def load_script(path):
    with open(path) as f:
        return json.load(f)

def to_markdown(data):
    out = [f"# {data.get('title', '?')}\n"]
    out.append(f"**Hook:** {data.get('hook', '')}\n")
    for i, s in enumerate(data.get("sections", []), 1):
        out.append(f"\n## {i}. {s.get('heading', '')}\n")
        out.append(s.get("content", ""))
    out.append(f"\n---\n")
    out.append(f"**Thumbnail:** {data.get('thumbnail_text', '')}")
    out.append(f"**Tags:** {', '.join(data.get('tags', []))}")
    out.append(f"\n**Description:**\n{data.get('description', '')}")
    return "\n".join(out)

def _fmt_srt(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def to_srt(data, wpm=150):
    out = []
    time = 0.0
    idx = 1
    hook = data.get("hook", "")
    if hook:
        dur = len(hook.split()) / wpm * 60
        out.append(f"{idx}\n{_fmt_srt(time)} --> {_fmt_srt(time + dur)}\n{hook}\n")
        time += dur + 0.5
        idx += 1
    for s in data.get("sections", []):
        content = s.get("content", "")
        for sent in re.split(r"(?<=[.!?؟])\s+", content):
            sent = sent.strip()
            if not sent: continue
            dur = max(2, len(sent.split()) / wpm * 60)
            out.append(f"{idx}\n{_fmt_srt(time)} --> {_fmt_srt(time + dur)}\n{sent}\n")
            time += dur + 0.3
            idx += 1
    return "\n".join(out)

def to_txt(data):
    out = []
    if data.get("hook"):
        out.append(data["hook"])
        out.append("")
    for s in data.get("sections", []):
        out.append(s.get("content", ""))
        out.append("")
    return "\n".join(out)

def export_all(path):
    p = Path(path)
    data = load_script(p)
    base = p.with_suffix("")
    files = {}
    for fmt, fn, ext in [("markdown", to_markdown, ".md"),
                          ("srt", to_srt, ".srt"),
                          ("txt", to_txt, ".txt")]:
        out = base.parent / (base.name + ext)
        with open(out, "w") as f:
            f.write(fn(data))
        files[fmt] = str(out)
        log.info(f"Exported {fmt}: {out}")
    return files

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(json.dumps(export_all(sys.argv[1]), indent=2))
