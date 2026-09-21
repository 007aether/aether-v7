#!/bin/bash
# Decrypt secrets at runtime, run bot, re-encrypt
KEY_FILE="/home/aether/.config/aether-secrets/.enc_key"
SECRETS_DIR="/home/aether/AETHER_Project"
ENCRYPTED_DIR="/home/aether/.config/aether-secrets"
VENV_PYTHON="/home/aether/AETHER_Project/.venv/bin/python3"

# Decrypt tokens for runtime
openssl enc -aes-256-cbc -d -pbkdf2 \
    -in "$ENCRYPTED_DIR/.bot_token.enc" \
    -out "$SECRETS_DIR/.bot_token" \
    -pass file:"$KEY_FILE" 2>/dev/null

openssl enc -aes-256-cbc -d -pbkdf2 \
    -in "$ENCRYPTED_DIR/.telegram_chat_id.enc" \
    -out "$SECRETS_DIR/.telegram_chat_id" \
    -pass file:"$KEY_FILE" 2>/dev/null

# Export token for bot.py
export TELEGRAM_BOT_TOKEN=$(cat "$SECRETS_DIR/.bot_token" 2>/dev/null)
export BOT_TOKEN="$TELEGRAM_BOT_TOKEN"

# Run the bot
cd /home/aether/AETHER_Project/aether-v7
exec "$VENV_PYTHON" -m src.bot

# Cleanup after bot exits
rm -f "$SECRETS_DIR/.bot_token" "$SECRETS_DIR/.telegram_chat_id" 2>/dev/null
