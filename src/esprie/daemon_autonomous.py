"""ESPRIEAETHER Autonomous Daemon - 24/24 Operation
Kite katkhdem kolchi b yedou bla intervention:
- Browser automation (Firefox + Selenium)
- Site signups & logins
- Telegram bot monitoring
- Aether service monitoring
- Airdrop scanning
- Content generation pipeline
- Trading monitoring
- Weekly reports
"""
import os
import sys
import time
import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/home/aether/AETHER_Project/aether-v7')
from src.esprie.core import TOOL_LIST
from src.esprie.tools import call as call_tool
from src.esprie.browser_automation import run_autonomous_tasks, create_driver
from src.utils import setup_logger, now

log = setup_logger("daemon_autonomous")

class AutonomousAgent:
    def __init__(self):
        self.running = True
        self.tasks_completed = 0
        self.last_heartbeat = datetime.now()
        
    def heartbeat(self):
        """Maintain heartbeat to system to prove liveness."""
        while self.running:
            self.last_heartbeat = datetime.now()
            log.info(f"[HEARTBEAT] Agent alive - {self.tasks_completed} tasks completed")
            time.sleep(60)  # Every 60 seconds
    
    def monitor_services(self):
        """Monitor all AETHER services."""
        while self.running:
            try:
                import subprocess
                result = subprocess.run(["systemctl", "is-active", "aether.service"], 
                                      capture_output=True, text=True)
                if result.stdout.strip() != "active":
                    log.warning("aether.service not active! Restarting...")
                    subprocess.run(["systemctl", "restart", "aether.service"])
            except Exception as e:
                log.error(f"Monitor error: {e}")
            time.sleep(300)  # Check every 5 min
    
    def scan_airdrops(self):
        """Scan airdrop eligibility every 30 minutes."""
        while self.running:
            try:
                result = call_tool("airdrops")
                log.info(f"Airdrop scan: {result}")
                self.tasks_completed += 1
            except Exception as e:
                log.error(f"Airdrop scan failed: {e}")
            time.sleep(1800)  # Every 30 min
    
    def auto_content_pipeline(self):
        """Auto-generate YouTube content."""
        while self.running:
            try:
                result = call_tool("plan")
                if result:
                    log.info(f"Content pipeline: planning new video")
                    result = call_tool("make_video", "AI")
                    self.tasks_completed += 1
            except Exception as e:
                log.error(f"Content pipeline failed: {e}")
            time.sleep(3600)  # Every hour
    
    def browser_automation_loop(self):
        """Autonomous browser tasks."""
        while self.running:
            try:
                tasks = [
                    {"action": "check", "url": "https://github.com/007aether/aether-v7"},
                    {"action": "scrape", "url": "https://api.github.com/repos/007aether/aether-v7"},
                ]
                results = run_autonomous_tasks(tasks)
                log.info(f"Browser automation: {len(results)} tasks done")
                self.tasks_completed += 1
            except Exception as e:
                log.error(f"Browser automation failed: {e}")
            time.sleep(3600)  # Every hour
    
    def telegram_monitor(self):
        """Monitor Telegram bot status."""
        while self.running:
            try:
                result = subprocess.run(["systemctl", "is-active", "aether-bot.service"],
                                      capture_output=True, text=True)
                if result.stdout.strip() != "active":
                    log.warning("Bot inactive! Restarting...")
                    subprocess.run(["systemctl", "restart", "aether-bot.service"])
            except Exception as e:
                log.error(f"Telegram monitor error: {e}")
            time.sleep(60)
    
    def run(self):
        """Start all autonomous loops."""
        log.info("🧠 ESPRIEAETHER Autonomous Agent STARTING...")
        log.info(f"Tools available: {TOOL_LIST}")
        
        # Start heartbeat thread
        hb = threading.Thread(target=self.heartbeat, daemon=True)
        hb.start()
        
        # Start service monitor
        svc = threading.Thread(target=self.monitor_services, daemon=True)
        svc.start()
        
        # Start airdrop scanner
        air = threading.Thread(target=self.scan_airdrops, daemon=True)
        air.start()
        
        # Start content pipeline
        content = threading.Thread(target=self.auto_content_pipeline, daemon=True)
        content.start()
        
        # Start browser automation
        browser = threading.Thread(target=self.browser_automation_loop, daemon=True)
        browser.start()
        
        # Start telegram monitor
        tg = threading.Thread(target=self.telegram_monitor, daemon=True)
        tg.start()
        
        # Main loop
        log.info("✅ All autonomous agents running - 24/7")
        while self.running:
            time.sleep(10)
            log.info(f"[STATUS] Tasks completed: {self.tasks_completed}, Heartbeat: {self.last_heartbeat.strftime('%H:%M:%S')}")

if __name__ == "__main__":
    agent = AutonomousAgent()
    try:
        agent.run()
    except KeyboardInterrupt:
        agent.running = False
        log.info("🧠 ESPRIEAETHER Autonomous Agent STOPPED")
