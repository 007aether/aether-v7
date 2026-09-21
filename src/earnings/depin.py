"""AETHER v9.3 — DePIN scanner (docker + native services)"""
import subprocess, json, sqlite3
from ..config import DB_PATH
from ..utils import now, setup_logger

log = setup_logger("depin")

PROVIDERS = {
    "PacketStream": {
        "type": "docker",
        "container": "packetstream",
        "daily_usd": 1.0,
        "cmd": ["docker", "run", "-d", "--name", "packetstream",
                "--restart", "unless-stopped",
                "-e", "CID=85HJ", "packetstream/psclient"],
        "note": "bandwidth sharing",
    },
    "Honeygain": {
        "type": "docker",
        "container": "honeygain",
        "daily_usd": 0.15,
        "cmd": None,
        "note": "bandwidth sharing",
    },
    "EarnApp": {
        "type": "native",
        "services": ["earnapp"],
        "processes": ["earnapp"],
        "daily_usd": 0.5,
        "cmd": None,
        "note": "bandwidth sharing (native)",
    },
    "Mysterium": {
        "type": "native",
        "services": ["mysterium-node"],
        "processes": ["mysterium_server"],
        "daily_usd": 1.5,
        "cmd": None,
        "note": "VPN node (native)",
    },
    "Repocket": {
        "type": "docker",
        "container": "repocket",
        "daily_usd": 0.5,
        "cmd": None,
        "note": "bandwidth sharing",
    },
    "Flux": {
        "type": "docker",
        "container": "flux",
        "daily_usd": 5.0,
        "cmd": None,
        "note": "compute node",
    },
    "Akash": {
        "type": "docker",
        "container": "akash",
        "daily_usd": 3.0,
        "cmd": None,
        "note": "GPU/compute marketplace",
    },
    "Nodepay": {
        "type": "manual",
        "daily_usd": 3.0,
        "cmd": None,
        "note": "AI bandwidth (desktop)",
    },
    "Grass": {
        "type": "manual",
        "daily_usd": 1.0,
        "cmd": None,
        "note": "AI scraping (extension)",
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


def _list_containers(tool):
    try:
        r = subprocess.run(
            [tool, "ps", "-a", "--format", "{{.Names}}|{{.Status}}"],
            capture_output=True, text=True, timeout=10,
        )
        out = {}
        for line in r.stdout.strip().split("\n"):
            if "|" in line:
                n, st = line.split("|", 1)
                out[n.strip()] = st.strip()
        return out
    except FileNotFoundError:
        return None
    except Exception as e:
        log.debug(f"{tool}: {e}")
        return {}


def _systemctl_active(unit):
    try:
        r = subprocess.run(["systemctl", "is-active", unit],
                           capture_output=True, text=True, timeout=5)
        return r.stdout.strip() == "active"
    except Exception:
        return False


def _pgrep(name):
    try:
        r = subprocess.run(["pgrep", "-f", name],
                           capture_output=True, text=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def check_docker(container_name):
    if not container_name:
        return "manual"
    for tool in ["docker", "podman"]:
        containers = _list_containers(tool)
        if containers is None:
            continue
        if container_name in containers:
            status = containers[container_name]
            if status.startswith("Up"):
                return "running"
            return "stopped"
    return "stopped"


def check_native(services=None, processes=None):
    for s in (services or []):
        if _systemctl_active(s):
            return "running"
    for p in (processes or []):
        if _pgrep(p):
            return "running"
    return "stopped"


def check_provider(info):
    t = info.get("type", "docker")
    if t == "manual":
        return "manual"
    if t == "native":
        return check_native(info.get("services"), info.get("processes"))
    return check_docker(info.get("container"))


def scan():
    ensure_table()
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.execute("DELETE FROM depin_providers")
    running = 0
    results = []
    for name, info in PROVIDERS.items():
        st = check_provider(info)
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
        "estimated_daily_usd": round(total_daily, 2),
        "providers": results,
    }


def start_provider(name):
    p = PROVIDERS.get(name)
    if not p or not p.get("cmd"):
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


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "install":
        results = {}
        for n in PROVIDERS:
            if check_provider(PROVIDERS[n]) == "running":
                results[n] = "already running"
            elif PROVIDERS[n].get("cmd"):
                results[n] = "started" if start_provider(n) else "failed"
            else:
                results[n] = "manual"
        print(json.dumps(results, indent=2))
    else:
        print(json.dumps(scan(), indent=2, ensure_ascii=False))
