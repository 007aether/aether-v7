#!/bin/bash
V7="/home/aether/AETHER_Project/aether-v7"
PY="/home/aether/AETHER_Project/.venv/bin/python3"

cd "$V7" || exit 1

case "${1:-help}" in
  init)       exec $PY -c "from src.db import init_all; init_all()" ;;
  migrate)    exec $PY scripts/migrate_old.py ;;
  status)     exec $PY -c "
from src.db import connect_memory, connect_earnings
cm = connect_memory(); ce = connect_earnings()
print('Cycles:', cm.execute('SELECT COUNT(*) FROM cycles').fetchone()[0])
print('Events:', cm.execute('SELECT COUNT(*) FROM events').fetchone()[0])
print('Skills:', cm.execute('SELECT COUNT(*) FROM skills').fetchone()[0])
print('Memory:', cm.execute('SELECT COUNT(*) FROM memory').fetchone()[0])
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
  health)     exec $PY -c "
import subprocess, requests, sqlite3
from src.config import DB_PATH, EARNINGS_DB, OLLAMA_URL

print('═══ AETHER v7 HEALTH ═══')
# Ollama
try:
    r = requests.get(OLLAMA_URL.replace('/generate','/tags'), timeout=5)
    models = [m['name'] for m in r.json().get('models', [])]
    print(f'✓ Ollama: {len(models)} models ({models[:3]})')
except Exception as e:
    print(f'✗ Ollama: {e}')
# DB
for label, p in [('Memory', DB_PATH), ('Earnings', EARNINGS_DB)]:
    try:
        c = sqlite3.connect(p); n = c.execute(\"SELECT COUNT(*) FROM sqlite_master WHERE type='table'\").fetchone()[0]
        c.close()
        print(f'✓ {label} DB: {n} tables at {p}')
    except Exception as e:
        print(f'✗ {label} DB: {e}')
# Services
for svc in ['aether-v7-daemon','aether-v7-bot','aether-v7-dashboard']:
    r = subprocess.run(['systemctl','--user','is-active',svc], capture_output=True, text=True)
    st = r.stdout.strip()
    icon = '✓' if st == 'active' else '✗'
    print(f'{icon} {svc}: {st}')
for svc in ['aether-v7-earner.timer','aether-v7-brain.timer']:
    r = subprocess.run(['systemctl','--user','is-active',svc], capture_output=True, text=True)
    st = r.stdout.strip()
    icon = '✓' if st == 'active' else '✗'
    print(f'{icon} {svc}: {st}')
" ;;
  logs)       tail -30 "$V7/data/logs/${2:-daemon}.log" ;;
  restart)    systemctl --user restart aether-v7-daemon aether-v7-bot aether-v7-dashboard
              echo "✓ Restarted" ;;
  test)       
    echo "═══ Test brain ═══"; $PY -m src.brain
    echo ""; echo "═══ Test earner ═══"; $PY -m src.earner
    ;;
  *)          echo "Usage: aether {init|migrate|status|brain|daemon|earner|bot|dashboard|health|logs <name>|restart|test}" ;;
esac
