"""ESPRIEAETHER MCP Server (FastMCP) - expose AETHER tools to Hermes"""
import json
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

ROOT = Path("/home/aether/AETHER_Project/aether-v7").resolve()
mcp = FastMCP("esprieaether")


def _run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True,
                           text=True, timeout=timeout, cwd=str(ROOT))
        return {"ok": r.returncode == 0,
                "stdout": r.stdout[-4000:],
                "stderr": r.stderr[-2000:],
                "rc": r.returncode}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _safe(rel):
    """Rje3 path absolut ila howa f projet, sinon None."""
    p = Path(rel)
    if not p.is_absolute():
        p = ROOT / p
    p = p.resolve()
    try:
        p.relative_to(ROOT)
    except ValueError:
        return None
    return p


@mcp.tool()
def list_files(path: str = ".") -> str:
    """List files in a directory inside the AETHER project. Default: project root."""
    p = _safe(path)
    if p is None:
        return "ERROR: path outside project"
    if not p.exists():
        return f"ERROR: {p} does not exist"
    if p.is_file():
        return f"FILE: {p} ({p.stat().st_size} bytes)"
    items = []
    for child in sorted(p.iterdir()):
        kind = "DIR " if child.is_dir() else "FILE"
        size = child.stat().st_size if child.is_file() else 0
        items.append(f"{kind}  {child.name}  ({size}b)")
    return "\n".join(items[:200])


@mcp.tool()
def read_file(path: str) -> str:
    """Read a file inside the AETHER project."""
    p = _safe(path)
    if p is None:
        return "ERROR: path outside project"
    if not p.exists():
        return f"ERROR: {p} does not exist"
    if p.is_dir():
        return f"ERROR: {p} is a directory, use list_files"
    try:
        return p.read_text()[:8000]
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def depin_scan() -> str:
    """Scan DePIN providers (PacketStream, Honeygain, EarnApp, Mysterium...) and return status."""
    r = _run("python3 -m src.earnings.depin", timeout=60)
    return json.dumps(r, indent=2)


@mcp.tool()
def depin_start(name: str) -> str:
    """Start a DePIN provider by name (PacketStream, Repocket, ...)."""
    r = _run(f"python3 -m src.earnings.depin install", timeout=90)
    return json.dumps(r, indent=2)


@mcp.tool()
def system_status() -> str:
    """Get system status: docker containers, services, git log."""
    out = {}
    out["docker"] = _run("docker ps --format '{{.Names}}|{{.Status}}'")
    out["services"] = _run("systemctl is-active aether earnapp ollama 2>/dev/null")
    out["git"] = _run("git log --oneline -3")
    return json.dumps(out, indent=2)


@mcp.tool()
def aether_brain(question: str) -> str:
    """Ask the local AETHER brain (ESPRIEAETHER AI) a question."""
    q = question.replace('"', '\\"')
    r = _run(f'aether brain "{q}"', timeout=180)
    return json.dumps(r, indent=2)


@mcp.tool()
def send_telegram(text: str) -> str:
    """Send a Telegram message via AETHER bot."""
    esc = text.replace("'", "'\\''")
    cmd = (
        "TOKEN=$(cat ~/AETHER_Project/.bot_token); "
        "CHAT=$(cat ~/AETHER_Project/.telegram_chat_id); "
        f"curl -s -X POST \"https://api.telegram.org/bot${{TOKEN}}/sendMessage\" "
        f"-d \"chat_id=${{CHAT}}\" --data-urlencode 'text={esc}'"
    )
    r = _run(cmd, timeout=30)
    return json.dumps(r, indent=2)


@mcp.tool()
def git_status() -> str:
    """Get git status + recent log of AETHER project."""
    out = {}
    out["status"] = _run("git status --short --branch")
    out["log"] = _run("git log --oneline -5")
    return json.dumps(out, indent=2)


@mcp.tool()
def run_terminal(cmd: str) -> str:
    """Run a terminal command inside the AETHER project directory (max 60s)."""
    r = _run(cmd, timeout=60)
    return json.dumps(r, indent=2)


if __name__ == "__main__":
    mcp.run()
