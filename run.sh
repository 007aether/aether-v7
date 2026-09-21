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
for svc in ['aether-v7-daemon','aether-v7-bot','aether-v7-dashboard','aether-v7-alerts','aether-v7-watcher','aether-v7-market','aether-v7-weekly']:
    r = subprocess.run(['systemctl','--user','is-active',svc], capture_output=True, text=True)
    st = r.stdout.strip()
    icon = '✓' if st == 'active' else '✗'
    print(f'{icon} {svc}: {st}')
for svc in ['aether-v7-earner.timer','aether-v7-brain.timer','aether-v7-learning.timer','aether-v7-airdrops.timer','aether-v7-sync.timer','aether-v7-backup.timer','aether-v7-depin.timer','aether-v7-paper.timer']:
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
  watcher)    exec $PY -c "from src.alerts.watcher import check_once; import json; print(json.dumps(check_once(), indent=2))" ;;
  market)     exec $PY -c "from src.alerts.market import check_once; import json; print(json.dumps(check_once(), indent=2))" ;;
  weekly)     exec $PY -m src.alerts.weekly ;;
  backup)     exec $PY -m src.maintenance.backup ;;
  report)     exec $PY -c "from src.alerts.notifier import send_daily_report; send_daily_report()" ;;
  testmsg)    exec $PY -c "from src.alerts.notifier import send; send('⚡ اختبار من AETHER v7')" ;;
  depin)      exec $PY -m src.earnings.depin ;;
  depin_install) exec $PY -m src.earnings.depin install ;;
  paper)      exec $PY -m src.trading.hyperliquid_paper portfolio ;;
  paper_price) exec $PY -m src.trading.hyperliquid_paper price "${2:-BTC}" ;;
  paper_open) exec $PY -m src.trading.hyperliquid_paper open "${2:-BTC}" "${3:-buy}" "${4:-100}" ;;
  paper_close) exec $PY -m src.trading.hyperliquid_paper close "${2:-1}" ;;
  niches)     exec $PY -m src.content.youtube_niche ;;
  niche)      exec $PY -m src.content.youtube_niche "${2:-ai_tools}" ;;
  sync)       exec $PY -c "from src.earnings.sync import sync; sync()" ;;
  eligibility) exec $PY -m src.airdrops.eligibility ;;
  airdrops)   exec $PY -c "from src.airdrops.tracker import refresh; print('✓ tracked', refresh())" ;;
  learn)      exec $PY -c "from src.learning.analyzer import analyze_cycles; import json; print(json.dumps(analyze_cycles(),indent=2,ensure_ascii=False))" ;;
  portfolio)  exec $PY -m src.wallet.manager ;;
  chains)     exec $PY -m src.wallet.chains ;;
  gas)        exec $PY -m src.wallet.gas ;;
  wallet)     exec $PY -m src.wallet.manager ;;
  tts)        exec $PY -c "from src.voice.tts import test; print(test())" ;;
  *)          echo "Usage: aether {init|migrate|status|brain|daemon|earner|bot|dashboard|health|logs <name>|restart|test}" ;;
esac
