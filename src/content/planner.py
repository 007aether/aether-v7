"""AETHER v7.9 — Weekly content planner"""
import json, sqlite3
from datetime import datetime, timedelta
from ..config import DB_PATH
from ..utils import now, setup_logger

log = setup_logger("planner")

DEFAULT_TOPICS = [
    ("5 AI tools that make money in 2026", "ai_tools", "ar"),
    ("How to earn from DePIN — beginner guide", "crypto", "ar"),
    ("أفضل 7 طرق للربح من الإنترنت", "finance", "ar"),
    ("Hyperliquid trading for beginners", "crypto", "ar"),
    ("10 free AI tools you need to try", "ai_tools", "en"),
    ("Airdrops 2026 — complete guide", "crypto", "ar"),
    ("Passive income with crypto in 2026", "finance", "en"),
]

def ensure_table():
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.execute("""CREATE TABLE IF NOT EXISTS content_plan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT, scheduled_for TEXT, topic TEXT,
        niche TEXT, language TEXT, status TEXT DEFAULT 'pending',
        script_file TEXT
    )""")
    c.commit()
    c.close()

def generate_plan(week_start=None):
    ensure_table()
    if not week_start:
        today = datetime.now()
        days_ahead = (7 - today.weekday()) % 7 or 7
        week_start = today + timedelta(days=days_ahead)
    else:
        week_start = datetime.fromisoformat(week_start)

    c = sqlite3.connect(DB_PATH, timeout=10)
    c.execute("DELETE FROM content_plan WHERE scheduled_for >= ?",
              (week_start.date().isoformat(),))

    count = 0
    for i, (topic, niche, lang) in enumerate(DEFAULT_TOPICS[:7]):
        day = week_start + timedelta(days=i)
        scheduled = day.replace(hour=10, minute=0, second=0, microsecond=0)
        c.execute(
            "INSERT INTO content_plan (ts, scheduled_for, topic, niche, language) "
            "VALUES (?,?,?,?,?)",
            (now(), scheduled.isoformat(), topic, niche, lang),
        )
        count += 1
    c.commit()
    c.close()
    log.info(f"Generated plan: {count} items")
    return {"week_start": week_start.date().isoformat(), "items": count}

def list_plan():
    ensure_table()
    c = sqlite3.connect(DB_PATH, timeout=10)
    rows = c.execute(
        "SELECT id, scheduled_for, topic, niche, language, status, script_file "
        "FROM content_plan ORDER BY scheduled_for"
    ).fetchall()
    c.close()
    return [
        {"id": r[0], "when": r[1][:16], "topic": r[2], "niche": r[3],
         "lang": r[4], "status": r[5], "script": r[6]}
        for r in rows
    ]

def next_pending():
    ensure_table()
    c = sqlite3.connect(DB_PATH, timeout=10)
    r = c.execute(
        "SELECT id, topic, niche, language FROM content_plan "
        "WHERE status='pending' ORDER BY scheduled_for LIMIT 1"
    ).fetchone()
    c.close()
    return r

def mark_done(item_id, script_file):
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.execute("UPDATE content_plan SET status='done', script_file=? WHERE id=?",
              (script_file, item_id))
    c.commit()
    c.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "generate":
        print(json.dumps(generate_plan(), indent=2))
    else:
        for item in list_plan():
            print(f"[{item['when']}] {item['topic']} ({item['niche']}, {item['lang']}) — {item['status']}")
