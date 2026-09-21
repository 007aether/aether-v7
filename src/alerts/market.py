"""AETHER v7.5 — Market price alerts"""
import json, sqlite3, time
from datetime import datetime
from ..config import DB_PATH
from ..wallet.pricing import get_prices
from .notifier import send
from ..utils import now, setup_logger

log = setup_logger("market")

# thresholds (USD) — بدّلهم إلا بغيتي
THRESHOLDS = {
    "ETH":  {"above": 3000, "below": 2000},
    "SOL":  {"above": 150,  "below": 80},
    "BTC":  {"above": 100000, "below": 60000},
    "BNB":  {"above": 900, "below": 500},
    "POL":  {"above": 0.3, "below": 0.08},
}

def ensure_table():
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.execute("""CREATE TABLE IF NOT EXISTS price_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT, symbol TEXT, price REAL, direction TEXT, threshold REAL
    )""")
    c.commit()
    c.close()

def last_alert(symbol, direction):
    """يرجع آخر تنبيه (باش ما نكرروش)"""
    c = sqlite3.connect(DB_PATH, timeout=10)
    r = c.execute(
        "SELECT ts, price FROM price_alerts WHERE symbol=? AND direction=? "
        "ORDER BY id DESC LIMIT 1",
        (symbol, direction),
    ).fetchone()
    c.close()
    return r

def save_alert(symbol, price, direction, threshold):
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.execute(
        "INSERT INTO price_alerts (ts, symbol, price, direction, threshold) VALUES (?,?,?,?,?)",
        (now(), symbol, price, direction, threshold),
    )
    c.commit()
    c.close()

def is_recent(ts_str, minutes=60):
    """واش التنبيه من قريب؟"""
    if not ts_str:
        return False
    try:
        t = datetime.fromisoformat(ts_str)
        return (datetime.now() - t).total_seconds() < minutes * 60
    except Exception:
        return False

def check_once():
    ensure_table()
    prices = get_prices()
    alerts = []
    for symbol, rule in THRESHOLDS.items():
        price = prices.get(symbol)
        if price is None:
            continue
        # above
        if "above" in rule and price >= rule["above"]:
            last = last_alert(symbol, "above")
            if not (last and is_recent(last[0], 60)):
                msg = (
                    f"📈 *{symbol} ABOVE*\n"
                    f"Price: `${price:,.2f}` ≥ `${rule['above']:,.2f}`\n"
                    f"🕐 {datetime.now().strftime('%H:%M')}"
                )
                send(msg)
                save_alert(symbol, price, "above", rule["above"])
                alerts.append({"symbol": symbol, "dir": "above", "price": price})
        # below
        if "below" in rule and price <= rule["below"]:
            last = last_alert(symbol, "below")
            if not (last and is_recent(last[0], 60)):
                msg = (
                    f"📉 *{symbol} BELOW*\n"
                    f"Price: `${price:,.2f}` ≤ `${rule['below']:,.2f}`\n"
                    f"🕐 {datetime.now().strftime('%H:%M')}"
                )
                send(msg)
                save_alert(symbol, price, "below", rule["below"])
                alerts.append({"symbol": symbol, "dir": "below", "price": price})
    return alerts

def main():
    log.info("Market alerts started (checks every 5 min)")
    while True:
        try:
            alerts = check_once()
            if alerts:
                log.info(f"Alerts: {alerts}")
        except Exception as e:
            log.error(f"market: {e}")
        time.sleep(300)

if __name__ == "__main__":
    print(json.dumps(check_once(), indent=2))
