#!/bin/bash
# AETHER v7 launcher
V7="/home/aether/AETHER_Project/aether-v7"
PY="/home/aether/AETHER_Project/.venv/bin/python3"

cd "$V7"
case "${1:-help}" in
  init)       exec $PY -c "from src.db import init_all; init_all()" ;;
  migrate)    exec $PY scripts/migrate_old.py ;;
  status)     exec $PY -c "
from src.db import connect_memory, connect_earnings
cm = connect_memory(); ce = connect_earnings()
print('Cycles:', cm.execute('SELECT COUNT(*) FROM cycles').fetchone()[0])
print('Events:', cm.execute('SELECT COUNT(*) FROM events').fetchone()[0])
print('Earnings:', ce.execute('SELECT COUNT(*) FROM earnings').fetchone()[0])
print('Total \$:', ce.execute('SELECT COALESCE(SUM(amount),0) FROM earnings').fetchone()[0])
print('DePIN running:', ce.execute(\"SELECT COUNT(*) FROM depin_status WHERE status='running'\").fetchone()[0])
print('Tap ready:', ce.execute(\"SELECT COUNT(*) FROM tap_status WHERE status='ready'\").fetchone()[0])
cm.close(); ce.close()" ;;
  brain)      exec $PY -m src.brain ;;
  daemon)     exec $PY -m src.daemon ;;
  earner)     exec $PY -m src.earner ;;
  bot)        exec $PY -m src.bot ;;
  dashboard)  exec $PY -m src.dashboard ;;
  *)          echo "Usage: $0 {init|migrate|status|brain|daemon|earner|bot|dashboard}" ;;
esac
