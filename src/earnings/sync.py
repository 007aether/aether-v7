"""AETHER v7 — Sync earnings providers to DB"""
from ..db import connect_earnings
from ..utils import now, setup_logger
from .providers import check_all

log = setup_logger("sync")

DAILY_ESTIMATE = {
    "PacketStream": 1.0,
    "Mysterium":    1.5,
    "Grass":        1.0,
    "Nodepay":      3.0,
}

def sync():
    ce = connect_earnings()
    try:
        results = check_all()
        running = 0
        for name, info in results.items():
            st = "running" if info.get("running") else "stopped"
            if st == "running":
                running += 1
            ce.execute("DELETE FROM depin_status WHERE project=?", (name,))
            ce.execute(
                "INSERT INTO depin_status (ts, project, status, daily_usd) VALUES (?,?,?,?)",
                (now(), name, st, DAILY_ESTIMATE.get(name, 0.5)),
            )
        ce.commit()
        log.info(f"Synced {len(results)} providers, {running} running")
        return {"total": len(results), "running": running, "details": results}
    finally:
        ce.close()

if __name__ == "__main__":
    import json
    print(json.dumps(sync(), indent=2, ensure_ascii=False, default=str))
