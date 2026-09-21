"""AETHER v7.9 — Content worker (auto from plan)"""
import json
from .planner import next_pending, mark_done
from .generator import generate_script
from .exporter import export_all
from ..utils import setup_logger

log = setup_logger("content_worker")

def run_one():
    """يولد script واحد من الخطة"""
    item = next_pending()
    if not item:
        log.info("No pending items")
        return {"status": "empty"}

    item_id, topic, niche, lang = item
    log.info(f"Processing: {topic} ({niche}, {lang})")

    result = generate_script(topic, niche=niche, duration_min=5, language=lang)
    script_file = result["file"]

    # Export
    try:
        exports = export_all(script_file)
    except Exception as e:
        exports = {"error": str(e)}
        log.error(f"export: {e}")

    mark_done(item_id, script_file)
    log.info(f"✓ Done: {topic}")

    return {
        "id": item_id, "topic": topic, "niche": niche,
        "script": script_file, "exports": exports,
    }

if __name__ == "__main__":
    print(json.dumps(run_one(), indent=2, ensure_ascii=False))
