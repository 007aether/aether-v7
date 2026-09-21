"""AETHER v7 — Migrate data from old DBs"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
from src.config import OLD_MEM_DB, OLD_EAR_DB
from src.db import connect_memory, connect_earnings
from src.utils import now

def migrate_memory():
    if not OLD_MEM_DB.exists():
        print(f"[skip] {OLD_MEM_DB} missing")
        return 0
    old = sqlite3.connect(OLD_MEM_DB)
    new = connect_memory()
    count = 0
    try:
        rows = old.execute(
            "SELECT cycle_ts, observation, decision, action, success FROM autonomous_cycles"
        ).fetchall()
        for r in rows:
            try:
                new.execute(
                    "INSERT INTO cycles (ts, observation, decision, action, success) "
                    "VALUES (?,?,?,?,?)", r)
                count += 1
            except Exception:
                pass
    except Exception as e:
        print(f"memory: {e}")
    new.commit(); new.close(); old.close()
    print(f"✓ Migrated {count} cycles")
    return count

def migrate_earnings():
    if not OLD_EAR_DB.exists():
        print(f"[skip] {OLD_EAR_DB} missing")
        return 0
    old = sqlite3.connect(OLD_EAR_DB)
    new = connect_earnings()
    count = 0
    try:
        rows = old.execute(
            "SELECT timestamp, source, amount, currency, status, description FROM earnings"
        ).fetchall()
        for r in rows:
            try:
                new.execute(
                    "INSERT INTO earnings (ts, source, amount, currency, status, note) "
                    "VALUES (?,?,?,?,?,?)", r)
                count += 1
            except Exception:
                pass
    except Exception as e:
        print(f"earnings: {e}")
    new.commit(); new.close(); old.close()
    print(f"✓ Migrated {count} earnings")
    return count

if __name__ == "__main__":
    print("═══ Migrating old data ═══")
    migrate_memory()
    migrate_earnings()
    print("✓ Migration done")
