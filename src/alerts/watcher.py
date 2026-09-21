"""AETHER v7.4 — Incoming funds watcher"""
import json, sqlite3, time
from datetime import datetime
from ..config import ROOT, DB_PATH
from ..wallet.manager import eth_address_from_seed, eth_balance
from ..wallet import solana as sol
from ..wallet import pricing
from .notifier import send
from ..utils import now, setup_logger

log = setup_logger("watcher")

SECRETS = ROOT / ".wallet_secrets.json"

# تخزين آخر balance فـ DB
def ensure_table():
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.execute("""CREATE TABLE IF NOT EXISTS balance_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT, chain TEXT, address TEXT, balance REAL
    )""")
    c.commit()
    c.close()

def last_balance(chain, address):
    c = sqlite3.connect(DB_PATH, timeout=10)
    r = c.execute(
        "SELECT balance FROM balance_snapshots WHERE chain=? AND address=? "
        "ORDER BY id DESC LIMIT 1",
        (chain, address),
    ).fetchone()
    c.close()
    return r[0] if r else None

def save_balance(chain, address, balance):
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.execute(
        "INSERT INTO balance_snapshots (ts, chain, address, balance) VALUES (?,?,?,?)",
        (now(), chain, address, balance),
    )
    c.commit()
    c.close()

def load_secrets():
    try:
        return json.loads(SECRETS.read_text())
    except Exception:
        return {}

def check_once():
    """يتحقق مرة وحدة ويرسل notification إلا تغير الـ balance"""
    ensure_table()
    d = load_secrets()
    alerts = []

    # ETH
    if d.get("metamask_seed"):
        addr = eth_address_from_seed(d["metamask_seed"])
        if addr:
            bal = eth_balance(addr)
            prev = last_balance("ethereum", addr)
            if bal is not None:
                if prev is not None and bal > prev + 1e-9:
                    diff = bal - prev
                    usd = pricing.usd_value("ETH", diff)
                    msg = (
                        f"💰 *INCOMING ETH*\n"
                        f"Received: `+{diff:.6f} ETH`"
                        + (f" (~${usd:.2f})" if usd else "") + "\n"
                        f"New balance: `{bal:.6f} ETH`\n"
                        f"Address: `{addr[:10]}...{addr[-6:]}`"
                    )
                    send(msg)
                    alerts.append({"chain": "eth", "diff": diff})
                save_balance("ethereum", addr, bal)

    # SOL
    if d.get("phantom_seed"):
        addr = sol.address_from_seed(d["phantom_seed"])
        if addr:
            bal = sol.check_balance(addr)
            prev = last_balance("solana", addr)
            if bal is not None:
                if prev is not None and bal > prev + 1e-9:
                    diff = bal - prev
                    usd = pricing.usd_value("SOL", diff)
                    msg = (
                        f"💰 *INCOMING SOL*\n"
                        f"Received: `+{diff:.6f} SOL`"
                        + (f" (~${usd:.2f})" if usd else "") + "\n"
                        f"New balance: `{bal:.6f} SOL`\n"
                        f"Address: `{addr[:10]}...{addr[-6:]}`"
                    )
                    send(msg)
                    alerts.append({"chain": "sol", "diff": diff})
                save_balance("solana", addr, bal)

    return alerts

def main():
    log.info("Incoming funds watcher started (checks every 5 min)")
    while True:
        try:
            alerts = check_once()
            if alerts:
                log.info(f"Alerts: {alerts}")
        except Exception as e:
            log.error(f"watcher: {e}")
        time.sleep(300)

if __name__ == "__main__":
    main()
