"""AETHER v7.7 — DePIN multi-provider manager"""
import subprocess, json, sqlite3
from datetime import datetime
from ..config import DB_PATH
from ..utils import now, setup_logger

log = setup_logger("depin")

# DePIN providers (docker/podman commands)
PROVIDERS = {
    "PacketStream": {
        "container": "psclient",
        "daily_usd": 1.0,
        "cmd": ["podman", "run", "-d", "--name", "psclient",
                "packetstream/psclient"],
        "note": "bandwidth sharing",
    },
    "Mysterium": {
        "container": "mysterium-node",
        "daily_usd": 1.5,
        "cmd": ["podman", "run", "-d", "--name", "mysterium-node",
                "--cap-add", "NET_ADMIN",
                "-p", "4449:4449", "mysteriumnetwork/mysterium-node"],
        "note": "VPN node",
    },
    "Flux": {
        "container": "flux",
        "daily_usd": 5.0,
        "cmd": ["podman", "run", "-d", "--name", "flux",
                "runonflux/flux:latest"],
        "note": "compute node",
    },
    "Akash": {
        "container": "akash",
        "daily_usd": 3.0,
        "cmd": ["podman", "run", "-d", "--name", "akash",
                "ghcr.io/akash-network/provider:latest"],
        "note": "GPU/compute marketplace",
    },
    "Nodepay": {
        "container": "nodepay",
        "daily_usd": 3.0,
        "cmd": None,  # desktop app
        "note": "AI bandwidth",
    },
    "Grass": {
        "container": "grass",
        "daily_usd": 1.0,
        "cmd": None,  # browser extension
        "note": "AI web scraping",
    },
}

def ensure_table():
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.execute("""CREATE TABLE IF NOT EXISTS depin_providers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT, name TEXT, status TEXT, daily_usd REAL, note TEXT
    )""")
    c.commit()
    c.close()

def container_status(name):
    """شوف واش container خدام"""
    for tool in (["podman"], ["docker"]):
        try:
            r = subprocess.run(
                tool + ["ps", "--format", "{{.Names}}", "--filter",
                        f"name={name}"],
                capture_output=True, text=True, timeout=10,
            )
            if name.lower() in r.stdout.lower():
                return "running"
        except FileNotFoundError:
            continue
    return "stopped"

def start_provider(name):
    """يشغل provider إلا كان container موجود"""
    p = PROVIDERS.get(name)
    if not p or not p["cmd"]:
        log.warning(f"{name}: no command (desktop/extension only)")
        return False
    try:
        r = subprocess.run(p["cmd"], capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            log.info(f"{name}: started")
            return True
        log.error(f"{name}: {r.stderr[:200]}")
        return False
    except Exception as e:
        log.error(f"{name}: {e}")
        return False

def scan():
    """يفحص كل providers"""
    ensure_table()
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.execute("DELETE FROM depin_providers")
    running = 0
    results = []
    for name, info in PROVIDERS.items():
        st = container_status(name) if info["cmd"] else "manual"
        if st == "running":
            running += 1
        c.execute(
            "INSERT INTO depin_providers (ts, name, status, daily_usd, note) VALUES (?,?,?,?,?)",
            (now(), name, st, info["daily_usd"], info["note"]),
        )
        results.append({
            "name": name, "status": st,
            "daily_usd": info["daily_usd"], "note": info["note"],
        })
    c.commit()
    c.close()

    total_daily = sum(p["daily_usd"] for p in results if p["status"] == "running")
    log.info(f"DePIN scan: {running}/{len(PROVIDERS)} running, ~${total_daily}/day")
    return {
        "running": running, "total": len(PROVIDERS),
        "estimated_daily_usd": total_daily,
        "providers": results,
    }

def install_all():
    """يثبت كل containers الممكنة"""
    results = {}
    for name in PROVIDERS:
        if not PROVIDERS[name]["cmd"]:
            results[name] = "manual (desktop/extension)"
            continue
        if container_status(name) == "running":
            results[name] = "already running"
            continue
        results[name] = "started" if start_provider(name) else "failed"
    return results

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "install":
        print(json.dumps(install_all(), indent=2))
    else:
        print(json.dumps(scan(), indent=2, ensure_ascii=False))
