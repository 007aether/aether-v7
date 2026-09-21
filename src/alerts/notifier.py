"""AETHER v7 — Telegram alerts"""
import requests
from datetime import datetime
from ..config import TOKEN_FILE, ADMIN_FILE
from ..utils import setup_logger

log = setup_logger("alerts")

def _read(p):
    try:
        return p.read_text().strip()
    except Exception:
        return None

TOKEN = _read(TOKEN_FILE)
ADMIN = _read(ADMIN_FILE)

def send(text):
    if not TOKEN or not ADMIN:
        log.warning("Missing token/admin")
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": ADMIN, "text": text, "parse_mode": "Markdown"},
            timeout=15,
        )
        return r.status_code == 200
    except Exception as e:
        log.error(f"send: {e}")
        return False

def send_startup():
    return send(f"⚡ *AETHER v7 Online*\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def send_daily_report():
    from ..db import connect_memory, connect_earnings
    cm = connect_memory()
    ce = connect_earnings()
    try:
        cycles = cm.execute("SELECT COUNT(*) FROM cycles").fetchone()[0]
        events = cm.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        skills = cm.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
        total = ce.execute("SELECT COALESCE(SUM(amount),0) FROM earnings").fetchone()[0]
        today = datetime.now().strftime("%Y-%m-%d")
        td = ce.execute(
            "SELECT COALESCE(SUM(amount),0) FROM earnings WHERE ts LIKE ?",
            (f"{today}%",),
        ).fetchone()[0]
        depin = ce.execute(
            "SELECT COUNT(*) FROM depin_status WHERE status='running'"
        ).fetchone()[0]
        tap = ce.execute(
            "SELECT COUNT(*) FROM tap_status WHERE status='ready'"
        ).fetchone()[0]
        last = cm.execute(
            "SELECT decision FROM cycles ORDER BY id DESC LIMIT 1"
        ).fetchone()
        last_text = last[0][:100] if last and last[0] else "N/A"

        txt = (
            f"📊 *AETHER Daily Report*\n"
            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"🔄 Cycles: `{cycles}`\n"
            f"📋 Events: `{events}`\n"
            f"🧠 Skills: `{skills}`\n\n"
            f"💰 Total: `${total:.2f}`\n"
            f"📅 Today: `${td:.2f}`\n"
            f"⛏️ DePIN: `{depin}` running\n"
            f"🎯 Tap: `{tap}` ready\n\n"
            f"🧠 آخر قرار: _{last_text}_"
        )
        ok = send(txt)
        if ok:
            log.info("Daily report sent")
        return ok
    finally:
        cm.close()
        ce.close()
