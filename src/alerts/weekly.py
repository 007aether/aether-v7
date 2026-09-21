"""AETHER v7.5 — Weekly report (Sundays)"""
import time, sqlite3, subprocess
from datetime import datetime, timedelta
from ..config import DB_PATH, EARNINGS_DB, V7, LOGS
from .notifier import send
from ..wallet.manager import summary as wallet_summary
from ..wallet.pricing import get_prices
from ..utils import setup_logger

log = setup_logger("weekly")

def _q1(db, sql, params=()):
    try:
        c = sqlite3.connect(db, timeout=10)
        r = c.execute(sql, params).fetchone()
        c.close()
        return r[0] if r else 0
    except Exception:
        return 0

def generate_report():
    # الفترة: 7 أيام
    since = (datetime.now() - timedelta(days=7)).isoformat()

    # cycles فـ الأسبوع
    cycles_week = _q1(DB_PATH, "SELECT COUNT(*) FROM cycles WHERE ts >= ?", (since,))
    events_week = _q1(DB_PATH, "SELECT COUNT(*) FROM events WHERE ts >= ?", (since,))
    skills = _q1(DB_PATH, "SELECT COUNT(*) FROM skills")
    total_earn = _q1(EARNINGS_DB, "SELECT COALESCE(SUM(amount),0) FROM earnings")
    earn_week = _q1(EARNINGS_DB, "SELECT COALESCE(SUM(amount),0) FROM earnings WHERE ts >= ?", (since,))
    airdrops = _q1(EARNINGS_DB, "SELECT COUNT(*) FROM airdrops_active")

    # portfolio
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
    ptext = " • ".join(f"{k}=${v:,.2f}" for k, v in prices.items() if v) or "?"

    # git stats
    try:
        r = subprocess.run(
            ["git", "-C", str(V7), "log", "--since=7.days", "--oneline"],
            capture_output=True, text=True, timeout=10,
        )
        git_commits = len([l for l in r.stdout.strip().split("\n") if l])
    except Exception:
        git_commits = 0

    txt = (
        f"📅 *AETHER — Weekly Report*\n"
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 *الأسبوع:*\n"
        f"  🔄 Cycles: `{cycles_week}`\n"
        f"  📋 Events: `{events_week}`\n"
        f"  📝 Commits: `{git_commits}`\n\n"
        f"💰 *الأرباح:*\n"
        f"  📊 Total: `${total_earn:.2f}`\n"
        f"  📅 Week: `${earn_week:.2f}`\n"
        f"  🚀 Airdrops: `{airdrops}`\n\n"
        f"👛 *المحافظ:*\n{wtext}"
        f"  💵 Total: `${total_usd:.2f}`\n\n"
        f"💹 *الأسعار:*\n{ptext}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ AETHER v7.5"
    )
    return txt

def main():
    """يبعث كل أحد على 10:00"""
    log.info("Weekly reporter started (Sundays @ 10:00)")
    last_sent = None
    while True:
        try:
            now = datetime.now()
            key = now.strftime("%Y-%W")  # سنة-أسبوع
            if now.weekday() == 6 and now.hour == 10 and last_sent != key:
                log.info(f"Sending weekly report {key}")
                txt = generate_report()
                send(txt)
                last_sent = key
        except Exception as e:
            log.error(f"weekly: {e}")
        time.sleep(600)  # كل 10 دقائق

if __name__ == "__main__":
    print(generate_report())
