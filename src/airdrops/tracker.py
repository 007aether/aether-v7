"""AETHER v7 — Airdrop tracker"""
from ..db import connect_earnings
from ..utils import now, setup_logger

log = setup_logger("airdrops")

KNOWN = [
    {"name": "Monad",       "chain": "monad",       "status": "testnet"},
    {"name": "MegaETH",     "chain": "megaeth",     "status": "testnet"},
    {"name": "Berachain",   "chain": "berachain",   "status": "live"},
    {"name": "Linea",       "chain": "linea",       "status": "live"},
    {"name": "Scroll",      "chain": "scroll",      "status": "live"},
    {"name": "zkSync",      "chain": "zksync",      "status": "live"},
    {"name": "Soneium",     "chain": "soneium",     "status": "testnet"},
    {"name": "Hyperliquid", "chain": "hyperliquid", "status": "live"},
    {"name": "EigenLayer",  "chain": "eigenlayer",  "status": "live"},
    {"name": "Ethena",      "chain": "ethena",      "status": "live"},
]

def refresh():
    ce = connect_earnings()
    try:
        ce.execute("DELETE FROM airdrops_active")
        for a in KNOWN:
            ce.execute(
                "INSERT INTO airdrops_active (ts, name, chain, status) VALUES (?,?,?,?)",
                (now(), a["name"], a["chain"], a["status"]),
            )
        ce.commit()
        log.info(f"Tracked {len(KNOWN)} airdrops")
        return len(KNOWN)
    finally:
        ce.close()

def list_tracked():
    ce = connect_earnings()
    try:
        rows = ce.execute(
            "SELECT name, chain, status FROM airdrops_active ORDER BY name"
        ).fetchall()
        return [{"name": r[0], "chain": r[1], "status": r[2]} for r in rows]
    finally:
        ce.close()

if __name__ == "__main__":
    refresh()
    for a in list_tracked():
        print(f"  {a['name']:15} ({a['chain']:12}) — {a['status']}")
