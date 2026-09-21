import subprocess
import os
import sys
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from src.brain import think

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# جلب الـ Token بأي سمية كانت ف config.py أو البيئة
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
if not TOKEN:
    try:
        import src.config as cfg
        TOKEN = getattr(cfg, "TELEGRAM_BOT_TOKEN", None) or getattr(cfg, "BOT_TOKEN", None) or getattr(cfg, "TELEGRAM_TOKEN", None)
    except Exception:
        pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_prompt = update.message.text
    system_instruction = (
        "You are Hermes 3, the autonomous root executor of ESPRIEAETHER system. "
        "If the user asks to perform a system action (install, build agent, modify files, run command), "
        "respond with the exact Bash commands wrapped inside ```bash ... ```, alongside a clear explanation."
    )
    try:
        response = think(prompt=user_prompt, system_prompt=system_instruction)
        if "```bash" in response:
            cmd = response.split("```bash")[1].split("```")[0].strip()
            await update.message.reply_text(f"🤖 **Hermes 3 Executing:**\n`{cmd}`", parse_mode="Markdown")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            output = result.stdout if result.returncode == 0 else result.stderr
            clean_output = output[:3000] if output else "Command executed with no output."
            await update.message.reply_text(f"✅ **Execution Result:**\n```\n{clean_output}\n```", parse_mode="Markdown")
        else:
            await update.message.reply_text(response)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Error: Could not find Telegram Bot Token in src/config.py or environment variables!")
        sys.exit(1)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
