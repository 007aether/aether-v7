"""AETHER v7 — Earning providers"""
import subprocess
from ..utils import setup_logger

log = setup_logger("providers")

def _ps_names(tool):
    try:
        r = subprocess.run(tool + ["ps", "--format", "{{.Names}}"],
                          capture_output=True, text=True, timeout=10)
        return r.stdout.lower()
    except FileNotFoundError:
        return None
    except Exception as e:
        log.debug(f"{tool}: {e}")
        return ""

def packetstream_status():
    for tool in (["podman"], ["docker"]):
        names = _ps_names(tool)
        if names and ("psclient" in names or "packetstream" in names):
            return {"running": True, "tool": tool[0]}
    return {"running": False}

def mysterium_status():
    for tool in (["podman"], ["docker"]):
        names = _ps_names(tool)
        if names and "mysterium" in names:
            return {"running": True, "tool": tool[0]}
    return {"running": False}

def grass_status():
    try:
        r = subprocess.run(["pgrep", "-f", "grass"],
                          capture_output=True, text=True, timeout=5)
        return {"running": bool(r.stdout.strip())}
    except Exception:
        return {"running": False}

def nodepay_status():
    try:
        r = subprocess.run(["pgrep", "-f", "nodepay"],
                          capture_output=True, text=True, timeout=5)
        return {"running": bool(r.stdout.strip())}
    except Exception:
        return {"running": False}

PROVIDERS = {
    "PacketStream": packetstream_status,
    "Mysterium":    mysterium_status,
    "Grass":        grass_status,
    "Nodepay":      nodepay_status,
}

def check_all():
    out = {}
    for name, fn in PROVIDERS.items():
        try:
            out[name] = fn()
        except Exception as e:
            out[name] = {"running": False, "error": str(e)}
    return out
