"""AETHER v8.2 — Fast Telegram Bot"""
import asyncio, sqlite3, sys, subprocess, json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes,
)
from .config import TOKEN_FILE, ADMIN_FILE, V7, LOGS, DB_PATH, EARNINGS_DB
from .brain import ask, ask_deep
from .esprie.core import process as esprie_process
from .cache import cached
from .utils import setup_logger

log = setup_logger("bot")

def _read(p):
    try:
        return p.read_text().strip()
    except Exception:
        return None

TOKEN = _read(TOKEN_FILE)
_admin = _read(ADMIN_FILE)
ADMIN = int(_admin) if _admin and _admin.isdigit() else None

# ═══════════════════ HELPERS (direct imports, cached) ═══════════════════
def is_admin(u):
    return ADMIN is None or u.effective_chat.id == ADMIN

@cached(ttl=5)
def _stats():
    """إحصائيات (5s cache)"""
    cm = sqlite3.connect(DB_PATH, timeout=5)
    ce = sqlite3.connect(EARNINGS_DB, timeout=5)
    try:
        return {
            "cycles": cm.execute("SELECT COUNT(*) FROM cycles").fetchone()[0],
            "events": cm.execute("SELECT COUNT(*) FROM events").fetchone()[0],
            "skills": cm.execute("SELECT COUNT(*) FROM skills").fetchone()[0],
            "total": ce.execute("SELECT COALESCE(SUM(amount),0) FROM earnings").fetchone()[0],
            "depin": ce.execute("SELECT COUNT(*) FROM depin_status WHERE status='running'").fetchone()[0],
            "tap": ce.execute("SELECT COUNT(*) FROM tap_status WHERE status='ready'").fetchone()[0],
            "airdrops": ce.execute("SELECT COUNT(*) FROM airdrops_active").fetchone()[0],
        }
    except Exception as e:
        log.error(f"stats: {e}")
        return {"cycles": 0, "events": 0, "skills": 0, "total": 0,
                "depin": 0, "tap": 0, "airdrops": 0}
    finally:
        cm.close(); ce.close()

def _subprocess_run(args, timeout=60):
    """wrapper سريع"""
    try:
        r = subprocess.run(args, capture_output=True, text=True,
                           timeout=timeout, cwd=str(V7))
        return r.stdout or r.stderr or "()"
    except Exception as e:
        return f"err: {e}"

# ═══════════════════ BASIC ═══════════════════
async def cmd_start(u, c):
    if not is_admin(u): return
    kb = [[
        InlineKeyboardButton("📊 Status", callback_data="status"),
        InlineKeyboardButton("💰 Earnings", callback_data="earnings"),
    ], [
        InlineKeyboardButton("🔄 Cycles", callback_data="cycles"),
        InlineKeyboardButton("🎯 Airdrops", callback_data="airdrops"),
    ], [
        InlineKeyboardButton("⚙️ Services", callback_data="services"),
        InlineKeyboardButton("👛 Wallet", callback_data="wallet"),
    ], [
        InlineKeyboardButton("🧠 Ask AI", callback_data="ask_help"),
        InlineKeyboardButton("🔮 Hermes", callback_data="hermes_help"),
    ]]
    await u.message.reply_text(
        "⚡ *AETHER v8.2*\n\nأسرع + Hermes\n/help للأوامر الكاملة",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb),
    )

async def cmd_help(u, c):
    if not is_admin(u): return
    txt = """⚡ *AETHER v8.2 — Fast Bot*

*📊 Status:*
/status /health /services /uptime /version

*💰 Earnings:*
/earnings /balance /sync /report

*🔄 AI:*
/ask <سؤال> — qwen3 (سريع)
/deep <سؤال> — hermes3 (ذكي)
/hermes <سؤال> — Hermes CLI
/cycles /brain /learn /top

*🎯 Crypto:*
/wallet /portfolio /chains /gas /eligibility /airdrops

*🎬 Content:*
/make <topic> — فيديو كامل
/scripts /plan

*⚙️ Control:*
/restart /restart_bot /logs /testmsg"""
    await u.message.reply_text(txt, parse_mode="Markdown")

# ═══════════════════ STATUS (FAST) ═══════════════════
async def cmd_status(u, c):
    if not is_admin(u): return
    s = _stats()
    await u.message.reply_text(
        f"⚡ *STATUS*\n\n"
        f"🔄 `{s['cycles']}` cycles\n"
        f"📋 `{s['events']}` events\n"
        f"🧠 `{s['skills']}` skills\n"
        f"💰 `${s['total']:.2f}`\n"
        f"⛏️ `{s['depin']}` depin\n"
        f"🎯 `{s['airdrops']}` airdrops",
        parse_mode="Markdown",
    )

async def cmd_health(u, c):
    if not is_admin(u): return
    await u.message.reply_text("🔍 كنفحص...")
    out = await asyncio.to_thread(_subprocess_run, [sys.executable, "run.sh", "health"], 30)
    await u.message.reply_text(f"```\n{out[:3500]}\n```", parse_mode="Markdown")

async def cmd_services(u, c):
    if not is_admin(u): return
    out = ["⚙️ *Services:*\n"]
    for svc in ["daemon", "bot", "dashboard", "alerts", "watcher", "market", "weekly"]:
        try:
            r = subprocess.run(["systemctl", "--user", "is-active",
                                f"aether-v7-{svc}.service"],
                               capture_output=True, text=True, timeout=5)
            st = r.stdout.strip()
            out.append(f"{'✅' if st=='active' else '❌'} `{svc}`")
        except Exception:
            out.append(f"❓ `{svc}`")
    await u.message.reply_text("\n".join(out), parse_mode="Markdown")

async def cmd_uptime(u, c):
    if not is_admin(u): return
    try:
        r = subprocess.run(["uptime", "-p"], capture_output=True, text=True)
        up = r.stdout.strip()
    except Exception:
        up = "?"
    await u.message.reply_text(f"⏱ System up: `{up}`", parse_mode="Markdown")

async def cmd_version(u, c):
    if not is_admin(u): return
    try:
        r = subprocess.run(["git", "-C", str(V7), "log", "--oneline", "-1"],
                           capture_output=True, text=True, timeout=5)
        commit = r.stdout.strip()
    except Exception:
        commit = "?"
    await u.message.reply_text(f"⚡ v8.2 — `{commit}`", parse_mode="Markdown")

# ═══════════════════ EARNINGS (FAST) ═══════════════════
async def cmd_earnings(u, c):
    if not is_admin(u): return
    s = _stats()
    ce = sqlite3.connect(EARNINGS_DB)
    today = datetime.now().strftime("%Y-%m-%d")
    td = ce.execute("SELECT COALESCE(SUM(amount),0) FROM earnings WHERE ts LIKE ?",
                    (f"{today}%",)).fetchone()[0]
    last = ce.execute("SELECT source, amount FROM earnings ORDER BY id DESC LIMIT 5").fetchall()
    ce.close()
    txt = f"💰 *EARNINGS*\n\n📊 Total: `${s['total']:.2f}`\n📅 Today: `${td:.2f}`\n"
    for src, amt in last:
        txt += f"• {src}: `${amt:.2f}`\n"
    await u.message.reply_text(txt, parse_mode="Markdown")

async def cmd_balance(u, c):
    if not is_admin(u): return
    out = await asyncio.to_thread(_subprocess_run, [sys.executable, "run.sh", "wallet"], 30)
    await u.message.reply_text(f"```\n{out[:3000]}\n```", parse_mode="Markdown")

async def cmd_sync(u, c):
    if not is_admin(u): return
    out = await asyncio.to_thread(_subprocess_run, [sys.executable, "-c",
        "from src.earnings.sync import sync; print(sync())"], 30)
    await u.message.reply_text(f"```\n{out[:1500]}\n```", parse_mode="Markdown")

async def cmd_report(u, c):
    if not is_admin(u): return
    await u.message.reply_text("📤 كنرسل...")
    out = await asyncio.to_thread(_subprocess_run, [sys.executable, "-c",
        "from src.alerts.notifier import send_daily_report; print(send_daily_report())"], 30)
    await u.message.reply_text(f"✅ {out.strip()[:200]}")

# ═══════════════════ AI (FAST) ═══════════════════
async def cmd_ask(u, c):
    if not is_admin(u): return
    parts = (u.message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await u.message.reply_text("اكتب: /ask سؤالك"); return
    await u.message.reply_text("⚡ كنفكر...")
    ans = await asyncio.to_thread(ask, parts[1], None)
    await u.message.reply_text((ans or "...")[:3500])

async def cmd_deep(u, c):
    if not is_admin(u): return
    parts = (u.message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await u.message.reply_text("اكتب: /deep سؤالك"); return
    await u.message.reply_text("🧠 كنفكر عميق (hermes3)...")
    ans = await asyncio.to_thread(ask_deep, parts[1], None)
    await u.message.reply_text((ans or "...")[:3500])

async def cmd_hermes(u, c):
    """Hermes CLI integration"""
    if not is_admin(u): return
    parts = (u.message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await u.message.reply_text("اكتب: /hermes سؤالك"); return
    q = parts[1]
    await u.message.reply_text("🔮 Hermes كايفكر...")
    hermes_bin = "/home/aether/.hermes/hermes-agent/venv/bin/hermes"
    if not __import__("os").path.exists(hermes_bin):
        await u.message.reply_text(f"❌ Hermes ماشي مثبت فـ {hermes_bin}")
        return
    def run_hermes():
        try:
            r = subprocess.run(
                [hermes_bin, "ask", q],
                capture_output=True, text=True, timeout=180,
                cwd="/home/aether",
            )
            return r.stdout.strip() or r.stderr.strip() or "(no output)"
        except subprocess.TimeoutExpired:
            return "⏱ timeout (180s)"
        except Exception as e:
            return f"err: {e}"
    out = await asyncio.to_thread(run_hermes)
    await u.message.reply_text(f"🔮 *Hermes:*\n\n{(out or '...')[:3500]}", parse_mode="Markdown")

async def cmd_cycles(u, c):
    if not is_admin(u): return
    cm = sqlite3.connect(DB_PATH)
    rows = cm.execute("SELECT decision, success, ts FROM cycles ORDER BY id DESC LIMIT 10").fetchall()
    cm.close()
    txt = "🔄 *آخر 10:*\n\n"
    for dec, suc, ts in rows:
        icon = "✅" if suc else "❌"
        t = (ts or "")[11:19]
        txt += f"{icon} `{t}` — {(dec or '')[:60]}\n"
    await u.message.reply_text(txt, parse_mode="Markdown")

async def cmd_brain(u, c):
    if not is_admin(u): return
    await u.message.reply_text("🧠 دورة تفكير...")
    out = await asyncio.to_thread(_subprocess_run,
        [sys.executable, "-c", "from src.brain import think; print(think('فحص Telegram'))"], 120)
    await u.message.reply_text(f"🧠 {out.strip()[:500]}")

async def cmd_learn(u, c):
    if not is_admin(u): return
    await u.message.reply_text("📚 كنحلل...")
    out = await asyncio.to_thread(_subprocess_run, [sys.executable, "-c",
        "from src.learning.analyzer import analyze_cycles; import json; print(json.dumps(analyze_cycles(), indent=2))"], 30)
    await u.message.reply_text(f"```\n{out[:2500]}\n```", parse_mode="Markdown")

async def cmd_top(u, c):
    if not is_admin(u): return
    cm = sqlite3.connect(DB_PATH)
    r = cm.execute("SELECT value FROM memory WHERE key='learning::top_words'").fetchone()
    rate = cm.execute("SELECT value FROM memory WHERE key='learning::success_rate'").fetchone()
    cm.close()
    await u.message.reply_text(
        f"📊 Rate: `{rate[0] if rate else '?'}`\n\nTop: `{r[0] if r else '?'}`",
        parse_mode="Markdown")

# ═══════════════════ CRYPTO ═══════════════════
async def cmd_wallet(u, c):
    if not is_admin(u): return
    out = await asyncio.to_thread(_subprocess_run, [sys.executable, "run.sh", "wallet"], 30)
    await u.message.reply_text(f"```\n{out[:2500]}\n```", parse_mode="Markdown")

async def cmd_portfolio(u, c):
    if not is_admin(u): return
    out = await asyncio.to_thread(_subprocess_run, [sys.executable, "-c",
        "from src.wallet.manager import summary; import json; print(json.dumps(summary(), indent=2, ensure_ascii=False))"], 30)
    await u.message.reply_text(f"```\n{out[:2500]}\n```", parse_mode="Markdown")

async def cmd_chains(u, c):
    if not is_admin(u): return
    await u.message.reply_text("🌐 كنفحص 9 شبكات...")
    out = await asyncio.to_thread(_subprocess_run, [sys.executable, "-c",
        "from src.wallet.chains import check_all_chains; from src.wallet.manager import eth_address_from_seed; from src.wallet import solana as sol; from src.config import ROOT; import json; d=json.loads((ROOT/'.wallet_secrets.json').read_text()); eth=eth_address_from_seed(d.get('metamask_seed','')); sa=sol.address_from_seed(d.get('phantom_seed','')); print(json.dumps(check_all_chains(eth, sa), indent=2))"], 60)
    await u.message.reply_text(f"```\n{out[:3000]}\n```", parse_mode="Markdown")

async def cmd_gas(u, c):
    if not is_admin(u): return
    out = await asyncio.to_thread(_subprocess_run, [sys.executable, "-c",
        "from src.wallet.gas import all_gas; import json; print(json.dumps(all_gas(), indent=2))"], 60)
    await u.message.reply_text(f"```\n{out[:2500]}\n```", parse_mode="Markdown")

async def cmd_eligibility(u, c):
    if not is_admin(u): return
    await u.message.reply_text("🎯 كنفحص...")
    out = await asyncio.to_thread(_subprocess_run, [sys.executable, "-c",
        "from src.airdrops.eligibility import check_eligibility; import json; print(json.dumps(check_eligibility(), indent=2, ensure_ascii=False))"], 60)
    await u.message.reply_text(f"```\n{out[:3000]}\n```", parse_mode="Markdown")

async def cmd_airdrops(u, c):
    if not is_admin(u): return
    ce = sqlite3.connect(EARNINGS_DB)
    data = ce.execute("SELECT name, chain, status FROM airdrops_active ORDER BY name").fetchall()
    ce.close()
    txt = "🎯 *AIRDROPS*\n\n"
    for name, chain, status in data:
        icon = "🟢" if status == "live" else "🟡"
        txt += f"{icon} `{name}` ({chain})\n"
    await u.message.reply_text(txt, parse_mode="Markdown")

# ═══════════════════ CONTENT ═══════════════════
async def cmd_make(u, c):
    if not is_admin(u): return
    parts = (u.message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await u.message.reply_text("اكتب: /make <topic>"); return
    topic = parts[1]
    await u.message.reply_text(f"🎬 كنصنع فيديو: {topic}\n⏳ هادي كتاخد ~3 min...")
    out = await asyncio.to_thread(_subprocess_run, [sys.executable, "-c",
        f"from src.video.pipeline import make_video_from_topic; import json; print(json.dumps(make_video_from_topic({topic!r}, 5, 'ar'), indent=2, ensure_ascii=False))"], 400)
    await u.message.reply_text(f"```\n{out[-2000:]}\n```", parse_mode="Markdown")

async def cmd_scripts(u, c):
    if not is_admin(u): return
    out = await asyncio.to_thread(_subprocess_run, [sys.executable, "-c",
        "from src.content.generator import list_scripts; [print(s) for s in list_scripts()[:10]]"], 15)
    await u.message.reply_text(f"```\n{out[:2000]}\n```", parse_mode="Markdown")

async def cmd_plan(u, c):
    if not is_admin(u): return
    out = await asyncio.to_thread(_subprocess_run, [sys.executable, "-m", "src.content.planner"], 15)
    await u.message.reply_text(f"```\n{out[:2000]}\n```", parse_mode="Markdown")

# ═══════════════════ CONTROL ═══════════════════
async def cmd_restart(u, c):
    if not is_admin(u): return
    await u.message.reply_text("🔄 كنريستارت...")
    for svc in ["daemon", "bot", "dashboard", "alerts"]:
        subprocess.run(["systemctl", "--user", "restart", f"aether-v7-{svc}.service"],
                       capture_output=True, timeout=15)
    await u.message.reply_text("✅ Restarted")

async def cmd_restart_bot(u, c):
    if not is_admin(u): return
    await u.message.reply_text("🔄 bot...")
    subprocess.run(["systemctl", "--user", "restart", "aether-v7-bot.service"],
                   capture_output=True, timeout=15)
    await u.message.reply_text("✅")

async def cmd_restart_daemon(u, c):
    if not is_admin(u): return
    await u.message.reply_text("🔄 daemon...")
    subprocess.run(["systemctl", "--user", "restart", "aether-v7-daemon.service"],
                   capture_output=True, timeout=15)
    await u.message.reply_text("✅")

async def cmd_logs(u, c):
    if not is_admin(u): return
    parts = (u.message.text or "").split(maxsplit=1)
    name = parts[1].strip() if len(parts) > 1 else "daemon"
    lf = LOGS / f"{name}.log"
    if not lf.exists():
        await u.message.reply_text(f"❌ ما كاينش: {name}")
        return
    content = lf.read_text()[-3000:]
    await u.message.reply_text(f"📋 `{name}`:\n```\n{content}\n```", parse_mode="Markdown")

async def cmd_testmsg(u, c):
    if not is_admin(u): return
    out = await asyncio.to_thread(_subprocess_run, [sys.executable, "-c",
        "from src.alerts.notifier import send; print(send('⚡ اختبار v8.2'))"], 15)
    await u.message.reply_text(f"✅ {out.strip()[:100]}")

# ═══════════════════ CALLBACKS ═══════════════════
async def cb_handler(u, c):
    q = u.callback_query
    await q.answer()
    data = q.data
    class FakeMsg:
        text = f"/{data}"
        async def reply_text(self, *a, **kw):
            await q.message.reply_text(*a, **kw)
    class FakeUpd:
        message = FakeMsg()
        effective_chat = q.message.chat
    fake = FakeUpd()
    handlers = {
        "status": cmd_status, "earnings": cmd_earnings,
        "cycles": cmd_cycles, "airdrops": cmd_airdrops,
        "services": cmd_services, "wallet": cmd_wallet,
        "ask_help": lambda u,c: u.message.reply_text("اكتب: /ask سؤالك"),
        "hermes_help": lambda u,c: u.message.reply_text("اكتب: /hermes سؤالك"),
    }
    fn = handlers.get(data)
    if fn:
        try:
            await fn(fake, c)
        except Exception as e:
            await q.message.reply_text(f"err: {e}")

# ═══════════════════ FALLBACK ═══════════════════
async def on_msg(u, c):
    """كل رسالة → ESPRIEAETHER العقل الموحّد"""
    if not is_admin(u): return
    if not u.message.text or u.message.text.startswith("/"): return
    text = u.message.text.strip()
    await u.message.reply_text("🧠 ...")
    try:
        result = await asyncio.to_thread(esprie_process, text)
    except Exception as e:
        await u.message.reply_text(f"❌ {e}")
        return

    if result.get("type") == "tool":
        tool = result.get("tool", "?")
        out = result.get("result", "")
        await u.message.reply_text(
            f"🔧 *{tool}*\n```\n{out[:3500]}\n```",
            parse_mode="Markdown"
        )
    elif result.get("type") == "error":
        await u.message.reply_text(f"❌ {result.get('error','')[:500]}")
    else:
        reply = result.get("reply", "")
        await u.message.reply_text((reply or "...")[:3500])

async def cmd_esprie(u, c):
    """معلومات عن العقل"""
    if not is_admin(u): return
    from .esprie.core import info
    d = info()
    tools = ", ".join(d["tool_list"][:10]) + "..." if len(d["tool_list"]) > 10 else ", ".join(d["tool_list"])
    await u.message.reply_text(
        f"🧠 *{d['name']} {d['version']}*\n"
        f"Tools: `{d['tools']}`\n\n"
        f"`{tools}`",
        parse_mode="Markdown"
    )

# ═══════════════════ MAIN ═══════════════════
def main():
    if not TOKEN:
        log.error("no token")
        return
    log.info(f"Starting v8.2 fast bot (admin={ADMIN})")
    app = Application.builder().token(TOKEN).build()

    cmds = {
        "start": cmd_start, "help": cmd_help,
        "status": cmd_status, "health": cmd_health,
        "services": cmd_services, "uptime": cmd_uptime, "version": cmd_version,
        "earnings": cmd_earnings, "balance": cmd_balance,
        "sync": cmd_sync, "report": cmd_report,
        "ask": cmd_ask, "deep": cmd_deep, "hermes": cmd_hermes,
        "cycles": cmd_cycles, "brain": cmd_brain, "learn": cmd_learn, "top": cmd_top,
        "wallet": cmd_wallet, "portfolio": cmd_portfolio,
        "chains": cmd_chains, "gas": cmd_gas,
        "eligibility": cmd_eligibility, "airdrops": cmd_airdrops,
        "make": cmd_make, "scripts": cmd_scripts, "plan": cmd_plan,
        "esprie": cmd_esprie,
        "restart": cmd_restart, "restart_bot": cmd_restart_bot,
        "restart_daemon": cmd_restart_daemon,
        "logs": cmd_logs, "testmsg": cmd_testmsg,
    }
    for name, fn in cmds.items():
        app.add_handler(CommandHandler(name, fn))
    app.add_handler(CallbackQueryHandler(cb_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_msg))

    log.info("Polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
