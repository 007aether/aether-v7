"""AETHER v7 — Telegram Bot (comprehensive)"""
import asyncio, subprocess, sqlite3, os, sys
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes,
)
from .config import TOKEN_FILE, ADMIN_FILE, V7, LOGS, DB_PATH, EARNINGS_DB
from .brain import ask
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

# ═══════════════════════════ HELPERS ═══════════════════════════
def is_admin(u):
    return ADMIN is None or u.effective_chat.id == ADMIN

def q1(db, sql, params=()):
    try:
        c = sqlite3.connect(db, timeout=5)
        r = c.execute(sql, params).fetchone()
        c.close()
        return r[0] if r else 0
    except Exception:
        return 0

def rows(db, sql, params=()):
    try:
        c = sqlite3.connect(db, timeout=5)
        r = c.execute(sql, params).fetchall()
        c.close()
        return r
    except Exception:
        return []

def sysctl(action, svc):
    try:
        r = subprocess.run(
            ["systemctl", "--user", action, svc],
            capture_output=True, text=True, timeout=10,
        )
        return r.returncode == 0, r.stdout + r.stderr
    except Exception as e:
        return False, str(e)

def stats():
    return {
        "cycles": q1(DB_PATH, "SELECT COUNT(*) FROM cycles"),
        "events": q1(DB_PATH, "SELECT COUNT(*) FROM events"),
        "skills": q1(DB_PATH, "SELECT COUNT(*) FROM skills"),
        "memory": q1(DB_PATH, "SELECT COUNT(*) FROM memory"),
        "earnings": q1(EARNINGS_DB, "SELECT COUNT(*) FROM earnings"),
        "total": q1(EARNINGS_DB, "SELECT COALESCE(SUM(amount),0) FROM earnings"),
        "depin": q1(EARNINGS_DB, "SELECT COUNT(*) FROM depin_status WHERE status='running'"),
        "tap": q1(EARNINGS_DB, "SELECT COUNT(*) FROM tap_status WHERE status='ready'"),
        "airdrops": q1(EARNINGS_DB, "SELECT COUNT(*) FROM airdrops_active"),
    }

# ═══════════════════════════ BASIC ═══════════════════════════
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
        InlineKeyboardButton("📋 Logs", callback_data="logs"),
    ], [
        InlineKeyboardButton("🧠 Learn", callback_data="learn"),
        InlineKeyboardButton("👛 Wallet", callback_data="wallet"),
    ]]
    await u.message.reply_text(
        "⚡ *AETHER v7 Control Center* ⚡\n\n"
        "اختر أو اكتب /help للأوامر الكاملة",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb),
    )

async def cmd_help(u, c):
    if not is_admin(u): return
    text = """⚡ *AETHER v7 — الأوامر الكاملة*

*📊 الحالة والمعلومات:*
/status — إحصائيات سريعة
/health — فحص شامل
/services — الخدمات (4)
/timers — التايمرات (5)
/uptime — مدة التشغيل
/version — الإصدار

*💰 الأرباح:*
/earnings — الأرباح الكاملة
/balance — رصيد المحفظة
/report — إرسال تقرير يومي
/sync — مزامنة DePIN

*🔄 الدورات:*
/cycles — آخر 10 دورات
/brain — تشغيل دورة تفكير
/ask <سؤال> — سول الـ AI
/learn — تحليل + تعلم
/top — أكثر الكلمات تكراراً

*🎯 Airdrops:*
/airdrops — قائمة كاملة
/airdrops_refresh — تحديث

*👛 Wallet:*
/wallet — عناوين المحافظ

*⚙️ التحكم:*
/restart — ريستارت كلشي
/restart_bot — ريستارت bot
/restart_daemon — ريستارت daemon
/logs <name> — سجلات (daemon/bot/dashboard/alerts/earner/brain/learning/sync/airdrops)
/testmsg — اختبار الإرسال
/speak <نص> — TTS

*ℹ️ أخرى:*
/help — هذه القائمة
/start — القائمة الرئيسية"""
    await u.message.reply_text(text, parse_mode="Markdown")

# ═══════════════════════════ STATUS ═══════════════════════════
async def cmd_status(u, c):
    if not is_admin(u): return
    s = stats()
    await u.message.reply_text(
        f"⚡ *AETHER STATUS*\n"
        f"🕐 `{datetime.now().strftime('%H:%M:%S')}`\n\n"
        f"🔄 Cycles: `{s['cycles']}`\n"
        f"📋 Events: `{s['events']}`\n"
        f"🧠 Skills: `{s['skills']}`\n"
        f"💾 Memory: `{s['memory']}`\n\n"
        f"💰 Total: `${s['total']:.2f}`\n"
        f"⛏️ DePIN: `{s['depin']}` running\n"
        f"🎯 Tap: `{s['tap']}` ready\n"
        f"🚀 Airdrops: `{s['airdrops']}` tracked",
        parse_mode="Markdown",
    )

async def cmd_health(u, c):
    if not is_admin(u): return
    await u.message.reply_text("🔍 كنفحص...")
    try:
        r = subprocess.run(
            [sys.executable, "run.sh", "health"],
            capture_output=True, text=True, timeout=30,
            cwd=str(V7),
        )
        out = r.stdout[:3500] or r.stderr[:3500] or "لا نتيجة"
    except Exception as e:
        out = f"خطأ: {e}"
    await u.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")

async def cmd_uptime(u, c):
    if not is_admin(u): return
    try:
        r = subprocess.run(["uptime", "-p"], capture_output=True, text=True)
        up = r.stdout.strip() or "?"
    except Exception:
        up = "?"
    # uptime daemon
    try:
        r = subprocess.run(
            ["systemctl", "--user", "show", "aether-v7-daemon",
             "--property=ActiveEnterTimestamp"],
            capture_output=True, text=True,
        )
        since = r.stdout.strip().split("=")[1]
    except Exception:
        since = "?"
    await u.message.reply_text(
        f"⏱ *UPTIME*\n\nSystem: `{up}`\nDaemon since: `{since}`",
        parse_mode="Markdown",
    )

async def cmd_version(u, c):
    if not is_admin(u): return
    try:
        r = subprocess.run(
            ["git", "-C", str(V7), "log", "--oneline", "-1"],
            capture_output=True, text=True,
        )
        commit = r.stdout.strip()
    except Exception:
        commit = "?"
    await u.message.reply_text(
        f"⚡ *AETHER v7.1*\n\nCommit: `{commit}`\nPath: `{V7}`",
        parse_mode="Markdown",
    )

# ═══════════════════════════ SERVICES ═══════════════════════════
async def cmd_services(u, c):
    if not is_admin(u): return
    out = ["⚙️ *SERVICES*\n"]
    for svc in ["daemon", "bot", "dashboard", "alerts"]:
        name = f"aether-v7-{svc}"
        try:
            r = subprocess.run(
                ["systemctl", "--user", "is-active", f"{name}.service"],
                capture_output=True, text=True,
            )
            st = r.stdout.strip()
            icon = "✅" if st == "active" else "❌"
            out.append(f"{icon} `{svc}` — {st}")
        except Exception:
            out.append(f"❓ `{svc}`")
    await u.message.reply_text("\n".join(out), parse_mode="Markdown")

async def cmd_timers(u, c):
    if not is_admin(u): return
    try:
        r = subprocess.run(
            ["systemctl", "--user", "list-timers", "aether-v7*", "--no-pager"],
            capture_output=True, text=True, timeout=10,
        )
        out = r.stdout[:3500]
    except Exception as e:
        out = f"خطأ: {e}"
    await u.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")

# ═══════════════════════════ EARNINGS ═══════════════════════════
async def cmd_earnings(u, c):
    if not is_admin(u): return
    s = stats()
    today = datetime.now().strftime("%Y-%m-%d")
    today_total = q1(EARNINGS_DB,
                     "SELECT COALESCE(SUM(amount),0) FROM earnings WHERE ts LIKE ?",
                     (f"{today}%",))
    last = rows(EARNINGS_DB,
                "SELECT source, amount FROM earnings ORDER BY id DESC LIMIT 5")
    txt = (
        f"💰 *EARNINGS*\n\n"
        f"📊 Total: `${s['total']:.2f}`\n"
        f"📅 Today: `${today_total:.2f}`\n"
        f"⛏️ DePIN: `{s['depin']}` running\n"
        f"🎯 Tap: `{s['tap']}` ready\n\n"
        f"*آخر 5:*\n"
    )
    for src, amt in last:
        txt += f"• {src}: `${amt:.2f}`\n"
    await u.message.reply_text(txt, parse_mode="Markdown")

async def cmd_balance(u, c):
    if not is_admin(u): return
    await u.message.reply_text("👛 كنجيب الرصيد...")
    try:
        r = subprocess.run(
            [sys.executable, "run.sh", "wallet"],
            capture_output=True, text=True, timeout=30,
            cwd=str(V7),
        )
        out = r.stdout[:3000] or r.stderr[:3000]
    except Exception as e:
        out = f"خطأ: {e}"
    await u.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")

async def cmd_report(u, c):
    if not is_admin(u): return
    await u.message.reply_text("📤 كنرسل التقرير...")
    try:
        r = subprocess.run(
            [sys.executable, "-c",
             "from src.alerts.notifier import send_daily_report; send_daily_report()"],
            capture_output=True, text=True, timeout=30, cwd=str(V7),
        )
        if r.returncode == 0:
            await u.message.reply_text("✅ التقرير وصل")
        else:
            await u.message.reply_text(f"⚠️ فشل:\n`{r.stderr[:500]}`",
                                        parse_mode="Markdown")
    except Exception as e:
        await u.message.reply_text(f"خطأ: {e}")

async def cmd_sync(u, c):
    if not is_admin(u): return
    await u.message.reply_text("🔄 كنزامن...")
    try:
        r = subprocess.run(
            [sys.executable, "-c",
             "from src.earnings.sync import sync; import json; print(json.dumps(sync(), indent=2, ensure_ascii=False))"],
            capture_output=True, text=True, timeout=30, cwd=str(V7),
        )
        out = r.stdout[:2500] or r.stderr[:2500]
    except Exception as e:
        out = f"خطأ: {e}"
    await u.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")

# ═══════════════════════════ CYCLES / AI ═══════════════════════════
async def cmd_cycles(u, c):
    if not is_admin(u): return
    data = rows(DB_PATH,
                "SELECT decision, success, ts FROM cycles ORDER BY id DESC LIMIT 10")
    if not data:
        await u.message.reply_text("ما كايناش دورات")
        return
    txt = "🔄 *آخر 10 دورات:*\n\n"
    for dec, suc, ts in data:
        icon = "✅" if suc else "❌"
        t = (ts or "")[11:19]
        txt += f"{icon} `{t}` — {(dec or '')[:70]}\n"
    await u.message.reply_text(txt, parse_mode="Markdown")

async def cmd_brain(u, c):
    if not is_admin(u): return
    await u.message.reply_text("🧠 كنفكر...")
    try:
        r = subprocess.run(
            [sys.executable, "-c",
             "from src.brain import think; print(think('فحص من Telegram'))"],
            capture_output=True, text=True, timeout=120, cwd=str(V7),
        )
        out = r.stdout.strip() or r.stderr[:500]
    except Exception as e:
        out = f"خطأ: {e}"
    await u.message.reply_text(f"🧠 *القرار:*\n{out}", parse_mode="Markdown")

async def cmd_ask(u, c):
    if not is_admin(u): return
    parts = (u.message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await u.message.reply_text("اكتب: /ask سؤالك")
        return
    await u.message.reply_text("🧠 كنفكر...")
    ans = await asyncio.to_thread(ask, parts[1])
    await u.message.reply_text((ans or "...")[:3500])

async def cmd_learn(u, c):
    if not is_admin(u): return
    await u.message.reply_text("📚 كنحلل...")
    try:
        r = subprocess.run(
            [sys.executable, "-c",
             "from src.learning.analyzer import analyze_cycles; import json; print(json.dumps(analyze_cycles(), indent=2, ensure_ascii=False))"],
            capture_output=True, text=True, timeout=60, cwd=str(V7),
        )
        out = r.stdout[:3000] or r.stderr[:3000]
    except Exception as e:
        out = f"خطأ: {e}"
    await u.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")

async def cmd_top(u, c):
    if not is_admin(u): return
    r = rows(DB_PATH,
             "SELECT value FROM memory WHERE key='learning::top_words'")
    rate = rows(DB_PATH,
                "SELECT value FROM memory WHERE key='learning::success_rate'")
    txt = (
        f"📊 *LEARNING*\n\n"
        f"Success rate: `{rate[0][0] if rate else '?'}`\n\n"
        f"Top words:\n`{r[0][0] if r else '?'}`"
    )
    await u.message.reply_text(txt, parse_mode="Markdown")

# ═══════════════════════════ AIRDROPS ═══════════════════════════
async def cmd_airdrops(u, c):
    if not is_admin(u): return
    data = rows(EARNINGS_DB,
                "SELECT name, chain, status FROM airdrops_active ORDER BY name")
    if not data:
        await u.message.reply_text("ما كايناش airdrops — دير /airdrops_refresh")
        return
    txt = "🎯 *AIRDROPS*\n\n"
    for name, chain, status in data:
        icon = "🟢" if status == "live" else "🟡"
        txt += f"{icon} `{name}` ({chain}) — {status}\n"
    await u.message.reply_text(txt, parse_mode="Markdown")

async def cmd_airdrops_refresh(u, c):
    if not is_admin(u): return
    await u.message.reply_text("🔄 كنحدّث...")
    try:
        r = subprocess.run(
            [sys.executable, "-c",
             "from src.airdrops.tracker import refresh; print('✓', refresh(), 'airdrops')"],
            capture_output=True, text=True, timeout=30, cwd=str(V7),
        )
        out = r.stdout.strip() or r.stderr[:500]
    except Exception as e:
        out = f"خطأ: {e}"
    await u.message.reply_text(out)

# ═══════════════════════════ WALLET ═══════════════════════════
async def cmd_wallet(u, c):
    if not is_admin(u): return
    await u.message.reply_text("👛 كنقرا المحافظ...")
    try:
        r = subprocess.run(
            [sys.executable, "run.sh", "wallet"],
            capture_output=True, text=True, timeout=30, cwd=str(V7),
        )
        out = r.stdout[:2500] or r.stderr[:2500]
    except Exception as e:
        out = f"خطأ: {e}"
    await u.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")

# ═══════════════════════════ CONTROL ═══════════════════════════
async def cmd_restart(u, c):
    if not is_admin(u): return
    await u.message.reply_text("🔄 كنريستارت...")
    results = []
    for svc in ["daemon", "bot", "dashboard", "alerts"]:
        ok, _ = sysctl("restart", f"aether-v7-{svc}.service")
        results.append(f"{'✅' if ok else '❌'} {svc}")
    await u.message.reply_text("نتائج:\n" + "\n".join(results))

async def cmd_restart_bot(u, c):
    if not is_admin(u): return
    await u.message.reply_text("🔄 كنريستارت bot...")
    ok, _ = sysctl("restart", "aether-v7-bot.service")
    await u.message.reply_text("✅" if ok else "❌")

async def cmd_restart_daemon(u, c):
    if not is_admin(u): return
    await u.message.reply_text("🔄 كنريستارت daemon...")
    ok, _ = sysctl("restart", "aether-v7-daemon.service")
    await u.message.reply_text("✅" if ok else "❌")

async def cmd_logs(u, c):
    if not is_admin(u): return
    parts = (u.message.text or "").split(maxsplit=1)
    name = parts[1].strip() if len(parts) > 1 else "daemon"
    log_file = LOGS / f"{name}.log"
    if not log_file.exists():
        await u.message.reply_text(f"❌ ما كاينش: {name}\n\nمتوفر: daemon, bot, dashboard, alerts, earner, brain, learning, sync, airdrops")
        return
    try:
        content = log_file.read_text()[-3000:]
    except Exception as e:
        content = f"خطأ: {e}"
    await u.message.reply_text(f"📋 `{name}.log`:\n```\n{content}\n```",
                                parse_mode="Markdown")

async def cmd_testmsg(u, c):
    if not is_admin(u): return
    try:
        r = subprocess.run(
            [sys.executable, "-c",
             "from src.alerts.notifier import send; send('⚡ AETHER v7 — اختبار')"],
            capture_output=True, text=True, timeout=15, cwd=str(V7),
        )
        ok = "True" in r.stdout
    except Exception:
        ok = False
    await u.message.reply_text("✅" if ok else "❌")

async def cmd_speak(u, c):
    if not is_admin(u): return
    parts = (u.message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await u.message.reply_text("اكتب: /speak نص")
        return
    text = parts[1]
    try:
        from .voice.tts import speak
        ok = await asyncio.to_thread(speak, text)
        await u.message.reply_text("🔊" if ok else "❌ ما كاينش TTS")
    except Exception as e:
        await u.message.reply_text(f"خطأ: {e}")

# ═══════════════════════════ CALLBACKS ═══════════════════════════
async def cb_handler(u, c):
    q = u.callback_query
    await q.answer()
    data = q.data
    # صنع fake update للاستدعاء
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
        "services": cmd_services, "logs": lambda u, c: cmd_logs(u, c),
        "learn": cmd_learn, "wallet": cmd_wallet,
    }
    fn = handlers.get(data)
    if fn:
        try:
            await fn(fake, c)
        except Exception as e:
            await q.message.reply_text(f"خطأ: {e}")

# ═══════════════════════════ FALLBACK ═══════════════════════════
async def on_msg(u, c):
    if not is_admin(u): return
    if not u.message.text: return
    if u.message.text.startswith("/"): return
    ans = await asyncio.to_thread(ask, u.message.text)
    await u.message.reply_text((ans or "...")[:3500])

# ═══════════════════════════ MAIN ═══════════════════════════

# ═══════════════════════════ v7.2 ADDITIONS ═══════════════════════════
async def cmd_portfolio(u, c):
    if not is_admin(u): return
    await u.message.reply_text("👛 كنقرا المحافظ...")
    try:
        r = subprocess.run(
            [sys.executable, "-c",
             "from src.wallet.manager import summary; import json; print(json.dumps(summary(), indent=2, ensure_ascii=False))"],
            capture_output=True, text=True, timeout=30, cwd=str(V7),
        )
        out = r.stdout[:3000] or r.stderr[:3000]
    except Exception as e:
        out = f"خطأ: {e}"
    await u.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")

async def cmd_eligibility(u, c):
    if not is_admin(u): return
    await u.message.reply_text("🎯 كنفحص...")
    try:
        r = subprocess.run(
            [sys.executable, "-c",
             "from src.airdrops.eligibility import check_eligibility; import json; print(json.dumps(check_eligibility(), indent=2, ensure_ascii=False))"],
            capture_output=True, text=True, timeout=60, cwd=str(V7),
        )
        out = r.stdout[:3000] or r.stderr[:3000]
    except Exception as e:
        out = f"خطأ: {e}"
    await u.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")


# ═══════════════════════════ v7.3 ADDITIONS ═══════════════════════════
async def cmd_chains(u, c):
    if not is_admin(u): return
    await u.message.reply_text("🌐 كنفحص 9 شبكات...")
    try:
        r = subprocess.run(
            [sys.executable, "-c",
             "from src.wallet.chains import check_all_chains; from src.wallet.manager import eth_address_from_seed; from src.wallet import solana as sol; from src.config import ROOT; import json; d=json.loads((ROOT/'.wallet_secrets.json').read_text()); eth=eth_address_from_seed(d.get('metamask_seed','')); sa=sol.address_from_seed(d.get('phantom_seed','')); print(json.dumps(check_all_chains(eth, sa), indent=2, ensure_ascii=False))"],
            capture_output=True, text=True, timeout=60, cwd=str(V7),
        )
        out = r.stdout[:3500] or r.stderr[:2000]
    except Exception as e:
        out = f"خطأ: {e}"
    await u.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")

async def cmd_gas(u, c):
    if not is_admin(u): return
    await u.message.reply_text("⛽ كنفحص الـ gas...")
    try:
        r = subprocess.run(
            [sys.executable, "-c",
             "from src.wallet.gas import all_gas, cheapest; import json; print(json.dumps({'all': all_gas(), 'cheapest': cheapest()}, indent=2))"],
            capture_output=True, text=True, timeout=60, cwd=str(V7),
        )
        out = r.stdout[:3500] or r.stderr[:2000]
    except Exception as e:
        out = f"خطأ: {e}"
    await u.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")


async def cmd_watcher(u, c):
    if not is_admin(u): return
    await u.message.reply_text("🔍 كنفحص الرصيد...")
    try:
        r = subprocess.run(
            [sys.executable, "-c",
             "from src.alerts.watcher import check_once; import json; print(json.dumps(check_once(), indent=2))"],
            capture_output=True, text=True, timeout=60, cwd=str(V7),
        )
        out = r.stdout[:2000] or r.stderr[:1000] or "()"
    except Exception as e:
        out = f"خطأ: {e}"
    await u.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")


async def cmd_market(u, c):
    if not is_admin(u): return
    await u.message.reply_text("📈 كنفحص الأسعار...")
    try:
        r = subprocess.run(
            [sys.executable, "-c",
             "from src.alerts.market import check_once; import json; print(json.dumps(check_once(), indent=2))"],
            capture_output=True, text=True, timeout=30, cwd=str(V7),
        )
        out = r.stdout.strip() or "()"
    except Exception as e:
        out = f"خطأ: {e}"
    await u.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")

async def cmd_weekly(u, c):
    if not is_admin(u): return
    await u.message.reply_text("📅 كنصاوب التقرير...")
    try:
        r = subprocess.run(
            [sys.executable, "-c",
             "from src.alerts.weekly import generate_report; print(generate_report())"],
            capture_output=True, text=True, timeout=60, cwd=str(V7),
        )
        out = r.stdout[:3500] or r.stderr[:1500]
    except Exception as e:
        out = f"خطأ: {e}"
    await u.message.reply_text(out, parse_mode="Markdown")

async def cmd_backup(u, c):
    if not is_admin(u): return
    await u.message.reply_text("💾 كنعمل backup...")
    try:
        r = subprocess.run(
            [sys.executable, "-c",
             "from src.maintenance.backup import run; import json; print(json.dumps(run(), indent=2))"],
            capture_output=True, text=True, timeout=60, cwd=str(V7),
        )
        out = r.stdout[:2000] or r.stderr[:1000]
    except Exception as e:
        out = f"خطأ: {e}"
    await u.message.reply_text(f"```\n{out}\n```", parse_mode="Markdown")

def main():
    if not TOKEN:
        log.error(f"No token at {TOKEN_FILE}")
        return
    log.info(f"Starting bot (admin={ADMIN})")
    app = Application.builder().token(TOKEN).build()

    handlers = {
        "start": cmd_start, "help": cmd_help,
        "status": cmd_status, "health": cmd_health,
        "uptime": cmd_uptime, "version": cmd_version,
        "services": cmd_services, "timers": cmd_timers,
        "earnings": cmd_earnings, "balance": cmd_balance,
        "report": cmd_report, "sync": cmd_sync,
        "cycles": cmd_cycles, "brain": cmd_brain, "ask": cmd_ask,
        "learn": cmd_learn, "top": cmd_top,
        "airdrops": cmd_airdrops, "airdrops_refresh": cmd_airdrops_refresh,
        "wallet": cmd_wallet,
        "restart": cmd_restart, "restart_bot": cmd_restart_bot,
        "restart_daemon": cmd_restart_daemon,
        "logs": cmd_logs, "testmsg": cmd_testmsg, "speak": cmd_speak,
        "portfolio": cmd_portfolio,
        "eligibility": cmd_eligibility,
        "chains": cmd_chains,
        "gas": cmd_gas,
        "watcher": cmd_watcher,
        "market": cmd_market,
        "weekly": cmd_weekly,
        "backup": cmd_backup,
    }
    for name, fn in handlers.items():
        app.add_handler(CommandHandler(name, fn))
    app.add_handler(CallbackQueryHandler(cb_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_msg))

    log.info("Polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
