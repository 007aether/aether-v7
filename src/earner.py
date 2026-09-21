"""AETHER v7 — Earnings Tracker"""
import subprocess
from .db import connect_earnings
from .utils import now, setup_logger

log = setup_logger("earner")

TAP_BOTS = ["Blum", "Hamster", "TapSwap", "MemeFi",
            "PixelVerse", "DotCoin", "Notix", "YesCoin"]

DEPIN = [
    ("PacketStream", "psclient",  1.0),
    ("Mysterium",    "mysterium", 1.5),
    ("Nodepay",      "nodepay",   3.0),
    ("Grass",        "grass",     1.0),
    ("Flux",         "flux",      5.0),
]

def check_running(keyword):
    for tool in (["podman", "ps", "--format", "{{.Names}}"],
                 ["docker", "ps", "--format", "{{.Names}}"]):
        try:
            r = subprocess.run(tool, capture_output=True, text=True, timeout=10)
            if keyword.lower() in r.stdout.lower():
                return True
        except FileNotFoundError:
            pass
    return False

def cycle():
    c = connect_earnings()
    c.execute("DELETE FROM depin_status")
    running_count = 0
    for name, key, daily in DEPIN:
        st = "running" if check_running(key) else "stopped"
        if st == "running": running_count += 1
        c.execute("INSERT INTO depin_status (ts,project,status,daily_usd) VALUES (?,?,?,?)",
                  (now(), name, st, daily))
    c.execute("DELETE FROM tap_status")
    for bot in TAP_BOTS:
        c.execute("INSERT INTO tap_status (ts,bot,status) VALUES (?,?,?)",
                  (now(), bot, "ready"))
    total = c.execute("SELECT COALESCE(SUM(amount),0) FROM earnings").fetchone()[0]
    c.commit(); c.close()
    log.info(f"Earner cycle done. Total=${total:.2f} | DePIN running: {running_count}/{len(DEPIN)} | Tap: {len(TAP_BOTS)}")
    return {"total": total, "depin_running": running_count}

if __name__ == "__main__":
    cycle()
