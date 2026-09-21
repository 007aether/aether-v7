"""AETHER v7.5 — Auto backup (DBs)"""
import shutil, subprocess, sqlite3
from datetime import datetime
from pathlib import Path
from ..config import ROOT, DB_PATH, EARNINGS_DB
from ..utils import setup_logger

log = setup_logger("backup")
BACKUP_DIR = ROOT / "AETHER_backups"
KEEP_DAYS = 30

def ensure_dir():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def backup_one(src: Path, dst: Path):
    """backup آمن باستعمال sqlite3 .backup"""
    try:
        if not src.exists():
            return None
        with sqlite3.connect(str(src), timeout=10) as src_conn, \
             sqlite3.connect(str(dst), timeout=10) as dst_conn:
            src_conn.backup(dst_conn)
        return str(dst)
    except Exception as e:
        log.error(f"backup {src.name}: {e}")
        return None

def backup_dbs():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    day_dir = BACKUP_DIR / datetime.now().strftime("%Y-%m-%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, src in [("aether.db", DB_PATH), ("earnings.db", EARNINGS_DB)]:
        if not src.exists():
            continue
        dst = day_dir / f"{name}.{ts}"
        r = backup_one(src, dst)
        if r:
            out[name] = r
            log.info(f"Backed up {name} → {dst}")
    return out

def cleanup_old():
    if not BACKUP_DIR.exists():
        return 0
    removed = 0
    cutoff = datetime.now().timestamp() - KEEP_DAYS * 86400
    for d in BACKUP_DIR.iterdir():
        if d.is_dir() and d.stat().st_mtime < cutoff:
            try:
                shutil.rmtree(d)
                removed += 1
            except Exception as e:
                log.error(f"cleanup {d}: {e}")
    return removed

def run():
    ensure_dir()
    result = {
        "ts": datetime.now().isoformat(),
        "backed_up": backup_dbs(),
        "removed": cleanup_old(),
    }
    log.info(f"Backup done: {result}")
    return result

if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))
