"""AETHER v7 — Learn from past cycles"""
from collections import Counter
from ..db import connect_memory
from ..utils import now, setup_logger
from ..brain import remember

log = setup_logger("learning")

def analyze_cycles(limit=200):
    cm = connect_memory()
    try:
        rows = cm.execute(
            "SELECT decision, success FROM cycles ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    finally:
        cm.close()

    if not rows:
        return {"info": "no cycles"}

    words = Counter()
    success = sum(1 for _, s in rows if s)
    for dec, _ in rows:
        if not dec:
            continue
        for w in dec.split():
            w = w.strip(".,!?،؟:;\"'()").lower()
            if len(w) > 4:
                words[w] += 1

    top = words.most_common(10)
    rate = success / len(rows) if rows else 0

    remember("learning::success_rate", f"{rate:.2%}", "learning")
    remember("learning::top_words",
             ", ".join(f"{w}({c})" for w, c in top[:5]), "learning")
    remember("learning::last_analysis", now(), "learning")
    remember("learning::cycles_analyzed", str(len(rows)), "learning")

    log.info(f"Analyzed {len(rows)} cycles, rate={rate:.1%}, top={top[:3]}")
    return {"cycles": len(rows), "success_rate": rate, "top_words": top}

def suggest_improvements():
    cm = connect_memory()
    try:
        r = cm.execute(
            "SELECT value FROM memory WHERE key='learning::success_rate'"
        ).fetchone()
    finally:
        cm.close()
    if not r:
        return []
    try:
        rate = float(r[0].replace("%", ""))
    except Exception:
        return []
    tips = []
    if rate < 70:
        tips.append("Success rate منخفض → بدّل prompt ديال brain")
    elif rate > 95:
        tips.append("Success rate عالي → نزيدو مهام أعقد")
    return tips

if __name__ == "__main__":
    import json
    print(json.dumps(analyze_cycles(), indent=2, ensure_ascii=False))
