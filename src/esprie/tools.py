"""AETHER v9 — Tool registry (كل module = أداة)"""
import subprocess, sys, json, sqlite3
from pathlib import Path
from ..config import V7, DB_PATH, EARNINGS_DB

def _run(cmd, timeout=60):
    """تشغيل أمر فرعي"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, cwd=str(V7))
        return (r.stdout or r.stderr or "").strip()[:1500]
    except Exception as e:
        return f"err: {e}"

def _py(code, timeout=60):
    """تشغيل python -c"""
    return _run([sys.executable, "-c", code], timeout)

# ═══════════ الأدوات ═══════════
TOOLS = {
    "status": {
        "desc": "حالة النظام (cycles, earnings, services)",
        "fn": lambda: _stats(),
    },
    "earnings": {
        "desc": "الأرباح الكاملة",
        "fn": lambda: _py(
            "from src.earnings.sync import sync; print(sync())", 30),
    },
    "sync": {
        "desc": "مزامنة DePIN",
        "fn": lambda: _py(
            "from src.earnings.sync import sync; print(sync())", 30),
    },
    "airdrops": {
        "desc": "تحديث قائمة airdrops",
        "fn": lambda: _py(
            "from src.airdrops.tracker import refresh; print('✓', refresh())", 30),
    },
    "eligibility": {
        "desc": "فحص أهلية الـ airdrops",
        "fn": lambda: _py(
            "from src.airdrops.eligibility import check_eligibility; import json; print(json.dumps(check_eligibility(), indent=2, ensure_ascii=False))", 60),
    },
    "wallet": {
        "desc": "المحافظ ETH + SOL",
        "fn": lambda: _py(
            "from src.wallet.manager import summary; import json; print(json.dumps(summary(), indent=2, ensure_ascii=False))", 30),
    },
    "chains": {
        "desc": "9 شبكات RPC",
        "fn": lambda: _py(
            "from src.wallet.chains import check_all_chains; from src.wallet.manager import eth_address_from_seed; from src.wallet import solana as sol; from src.config import ROOT; import json; d=json.loads((ROOT/'.wallet_secrets.json').read_text()); print(json.dumps(check_all_chains(eth_address_from_seed(d.get('metamask_seed','')), sol.address_from_seed(d.get('phantom_seed',''))), indent=2))", 60),
    },
    "gas": {
        "desc": "أسعار الغاز",
        "fn": lambda: _py(
            "from src.wallet.gas import all_gas; import json; print(json.dumps(all_gas(), indent=2))", 60),
    },
    "learn": {
        "desc": "تحليل الدورات",
        "fn": lambda: _py(
            "from src.learning.analyzer import analyze_cycles; import json; print(json.dumps(analyze_cycles(), indent=2, ensure_ascii=False))", 30),
    },
    "market": {
        "desc": "فحص تنبيهات السوق",
        "fn": lambda: _py(
            "from src.alerts.market import check_once; print(check_once())", 30),
    },
    "report": {
        "desc": "إرسال تقرير يومي Telegram",
        "fn": lambda: _py(
            "from src.alerts.notifier import send_daily_report; print(send_daily_report())", 30),
    },
    "backup": {
        "desc": "backup DBs",
        "fn": lambda: _py(
            "from src.maintenance.backup import run; import json; print(json.dumps(run(), indent=2))", 60),
    },
    "services": {
        "desc": "حالة 7 services + 10 timers",
        "fn": lambda: _services(),
    },
    "plan": {
        "desc": "خطة المحتوى الأسبوعية",
        "fn": lambda: _py(
            "from src.content.planner import list_plan; [print(f\"[{p['when']}] {p['topic']}\") for p in list_plan()]", 15),
    },
    "content_run": {
        "desc": "توليد script من الخطة",
        "fn": lambda: _py(
            "from src.content.worker import run_one; import json; print(json.dumps(run_one(), indent=2, ensure_ascii=False))", 300),
    },
    "make_video": {
        "desc": "توليد فيديو من موضوع (topic)",
        "fn": lambda topic="5 AI tools 2026": _py(
            f"from src.video.pipeline import make_video_from_topic; import json; print(json.dumps(make_video_from_topic({topic!r}, 5, 'ar'), indent=2, ensure_ascii=False))", 400),
    },
    "depin": {
        "desc": "فحص DePIN providers",
        "fn": lambda: _py(
            "from src.earnings.depin import scan; import json; print(json.dumps(scan(), indent=2, ensure_ascii=False))", 60),
    },
    "hermes": {
        "desc": "Hermes CLI — سؤال عميق",
        "fn": lambda q="مرحبا": _hermes(q),
    },
}

def _stats():
    try:
        cm = sqlite3.connect(DB_PATH, timeout=5)
        ce = sqlite3.connect(EARNINGS_DB, timeout=5)
        out = {
            "cycles": cm.execute("SELECT COUNT(*) FROM cycles").fetchone()[0],
            "events": cm.execute("SELECT COUNT(*) FROM events").fetchone()[0],
            "skills": cm.execute("SELECT COUNT(*) FROM skills").fetchone()[0],
            "earnings_total": ce.execute("SELECT COALESCE(SUM(amount),0) FROM earnings").fetchone()[0],
            "depin_running": ce.execute("SELECT COUNT(*) FROM depin_status WHERE status='running'").fetchone()[0],
            "airdrops": ce.execute("SELECT COUNT(*) FROM airdrops_active").fetchone()[0],
        }
        cm.close(); ce.close()
        return json.dumps(out, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"err: {e}"

def _services():
    out = []
    for svc in ["daemon", "bot", "dashboard", "alerts", "watcher", "market", "weekly"]:
        r = subprocess.run(["systemctl", "--user", "is-active",
                            f"aether-v7-{svc}.service"],
                           capture_output=True, text=True, timeout=5)
        out.append(f"{svc}: {r.stdout.strip()}")
    return "\n".join(out)

HERMES_BIN = "/home/aether/.hermes/hermes-agent/venv/bin/hermes"

def _hermes(question):
    """يستدعي hermes CLI"""
    if not Path(HERMES_BIN).exists():
        return f"❌ Hermes ماشي مثبت: {HERMES_BIN}"
    try:
        r = subprocess.run(
            [HERMES_BIN, "ask", question],
            capture_output=True, text=True, timeout=180,
            cwd="/home/aether",
        )
        return (r.stdout or r.stderr or "").strip()[:2000]
    except subprocess.TimeoutExpired:
        return "⏱ Hermes timeout (180s)"
    except Exception as e:
        return f"err: {e}"

def list_tools():
    """لائحة الأدوات"""
    return [(name, info["desc"]) for name, info in TOOLS.items()]

def call(name, *args, **kwargs):
    """يستدعي أداة"""
    if name not in TOOLS:
        return f"❌ أداة غير معروفة: {name}"
    try:
        return TOOLS[name]["fn"](*args, **kwargs)
    except Exception as e:
        return f"err in {name}: {e}"

# ==========================================
# HERMES AGENT AUTOMATIC INTEGRATION TOOL
# ==========================================
import subprocess

def run_hermes_task(prompt: str) -> str:
    """إرسال مهمة تنفيذية معقدة لـ Hermes Agent للتنفيذ التلقائي"""
    try:
        cmd = f"hermes run \"{prompt}\" --quiet"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return result.stdout.strip()
        return f"Hermes Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Exec Exception: {str(e)}"
