"""AETHER v8.0 — Full video pipeline"""
import json
from pathlib import Path
from .assembler import assemble
from ..content.generator import generate_script
from ..content.exporter import export_all
from ..utils import setup_logger

log = setup_logger("video_pipeline")

def make_video_from_script(script_file, language="ar"):
    """script → voice + thumbnail + mp4"""
    log.info(f"=== Video pipeline: {script_file} ===")

    # 1. Export formats
    try:
        exports = export_all(script_file)
    except Exception as e:
        exports = {"error": str(e)}

    # 2. Build video
    result = assemble(script_file, language)

    return {
        "script": str(script_file),
        "exports": exports,
        "video": result,
    }

def make_video_from_topic(topic, duration=5, language="ar"):
    """topic → script → video (كامل من الصفر)"""
    log.info(f"=== Full pipeline: {topic} ===")

    # 1. Generate script
    gen = generate_script(topic, duration_min=duration, language=language)
    script_file = gen["file"]
    log.info(f"✓ script: {script_file}")

    # 2. Video
    return make_video_from_script(script_file, language)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: {script <file> [lang] | topic <topic> [min] [lang]}")
    elif sys.argv[1] == "script":
        r = make_video_from_script(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "ar")
        print(json.dumps(r, indent=2, ensure_ascii=False))
    elif sys.argv[1] == "topic":
        topic = sys.argv[2]
        dur = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        lang = sys.argv[4] if len(sys.argv) > 4 else "ar"
        r = make_video_from_topic(topic, dur, lang)
        print(json.dumps(r, indent=2, ensure_ascii=False))
