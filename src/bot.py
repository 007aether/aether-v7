"""AETHER v7 — Telegram Bot"""
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from .config import TOKEN_FILE, ADMIN_FILE
from .db import connect_memory, connect_earnings
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

def is_admin(u):
    return ADMIN is None or u.effective_chat.id == ADMIN

async def cmd_start(u, c):
    if not is_admin(u): return
    await u.message.reply_text(
        "⚡ *AETHER v7 Bot* ⚡\n\n"
        "/status — حالة النظام\n"
        "/earnings — الأرباح\n"
        "/cycles — آخر الدورات\n"
        "/ask <سؤال> — سول الـ AI",
        parse_mode="Markdown")

async def cmd_status(u, c):
    if not is_admin(u): return
    cm = connect_memory()
    cycles = cm.execute("SELECT COUNT(*) FROM cycles").fetchone()[0]
    events = cm.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    skills = cm.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
    cm.close()
    await u.message.reply_text(
        f"⚡ *AETHER STATUS*\n\n"
        f"🔄 Cycles: `{cycles}`\n"
        f"📋 Events: `{events}`\n"
        f"🧠 Skills: `{skills}`",
        parse_mode="Markdown")

async def cmd_earnings(u, c):
    if not is_admin(u): return
    ce = connect_earnings()
    total = ce.execute("SELECT COALESCE(SUM(amount),0) FROM earnings").fetchone()[0]
    depin = ce.execute("SELECT COUNT(*) FROM depin_status WHERE status='running'").fetchone()[0]
    tap = ce.execute("SELECT COUNT(*) FROM tap_status WHERE status='ready'").fetchone()[0]
    ce.close()
    await u.message.reply_text(
        f"💰 *EARNINGS*\n\n"
        f"Total: `${total:.2f}`\n"
        f"🎯 Tap: `{tap}`\n"
        f"⛏️ DePIN: `{depin}`",
        parse_mode="Markdown")

async def cmd_cycles(u, c):
    if not is_admin(u): return
    cm = connect_memory()
    rows = cm.execute("SELECT decision, ts FROM cycles ORDER BY id DESC LIMIT 5").fetchall()
    cm.close()
    lines = ["🔄 *آخر 5 دورات:*\n"]
    for d, ts in rows:
        lines.append(f"• `{ts[:16]}` — {(d or '')[:60]}")
    await u.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def cmd_ask(u, c):
    if not is_admin(u): return
    parts = u.message.text.split(maxsplit=1)
    if len(parts) < 2:
        await u.message.reply_text("اكتب: /ask سؤالك"); return
    await u.message.reply_text("🧠 كنفكر...")
    ans = await asyncio.to_thread(ask, parts[1])
    await u.message.reply_text((ans or "...")[:3500])

async def on_msg(u, c):
    if not is_admin(u): return
    if not u.message.text: return
    ans = await asyncio.to_thread(ask, u.message.text)
    await u.message.reply_text((ans or "...")[:3500])

def main():
    if not TOKEN:
        log.error(f"No token at {TOKEN_FILE}")
        return
    log.info(f"Starting bot (admin={ADMIN})")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("earnings", cmd_earnings))
    app.add_handler(CommandHandler("cycles", cmd_cycles))
    app.add_handler(CommandHandler("ask", cmd_ask))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_msg))
    log.info("Polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
