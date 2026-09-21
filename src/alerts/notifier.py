"""AETHER v7.4 — Telegram alerts (enhanced)"""
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
    return send(f"⚡ *AETHER v7.4 Online*\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def send_daily_report():
    from ..db import connect_memory, connect_earnings
    from ..wallet.manager import summary as wallet_summary
    from ..wallet.pricing import get_prices

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
        depin = ce.execute("SELECT COUNT(*) FROM depin_status WHERE status='running'").fetchone()[0]
        tap = ce.execute("SELECT COUNT(*) FROM tap_status WHERE status='ready'").fetchone()[0]
        airdrops = ce.execute("SELECT COUNT(*) FROM airdrops_active").fetchone()[0]
        last = cm.execute("SELECT decision FROM cycles ORDER BY id DESC LIMIT 1").fetchone()
        last_text = last[0][:100] if last and last[0] else "N/A"

        # wallet portfolio
        try:
            port = wallet_summary(include_balance=True)
            total_usd = port.get("total_usd", 0)
            wtext = ""
            for name, w in port.get("wallets", {}).items():
                bal = w.get("balance")
                if bal is None: continue
                usd = w.get("usd") or 0
                wtext += f"  • {name}: `{bal:.6f} {w['symbol']}` (~${usd:.2f})\n"
            if not wtext:
                wtext = "  (لا محافظ)\n"
        except Exception as e:
            wtext = f"  (خطأ: {e})\n"
            total_usd = 0

        prices = get_prices()
        ptext = ", ".join(f"{k}=${v:,.0f}" for k, v in prices.items() if v) or "?"

        txt = (
            f"📊 *AETHER v7.4 — Daily Report*\n"
            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚙️ *النظام:*\n"
            f"  🔄 Cycles: `{cycles}`\n"
            f"  📋 Events: `{events}`\n"
            f"  🧠 Skills: `{skills}`\n\n"
            f"💰 *الأرباح:*\n"
            f"  📊 Total: `${total:.2f}`\n"
            f"  📅 Today: `${td:.2f}`\n"
            f"  ⛏️ DePIN: `{depin}` running\n"
            f"  🎯 Tap: `{tap}` ready\n"
            f"  🚀 Airdrops: `{airdrops}` tracked\n\n"
            f"👛 *المحافظ:*\n{wtext}"
            f"  💵 Total: `${total_usd:.2f}`\n\n"
            f"💹 *الأسعار:*\n  {ptext}\n\n"
            f"🧠 آخر قرار: _{last_text}_"
        )
        ok = send(txt)
        if ok:
            log.info("Daily report sent")
        return ok
    finally:
        cm.close()
        ce.close()
