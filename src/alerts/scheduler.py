"""AETHER v7 — Alert scheduler (8:00 و 20:00)"""
import time
from datetime import datetime
from .notifier import send_daily_report
from ..utils import setup_logger

log = setup_logger("scheduler")

SEND_HOURS = {8, 20}

def main():
    log.info("Scheduler started (reports at 8:00 and 20:00)")
    last_sent = None
    while True:
        try:
            now = datetime.now()
            key = now.strftime("%Y-%m-%d %H")
            if now.hour in SEND_HOURS and last_sent != key:
                log.info(f"Sending daily report for {key}")
                try:
                    send_daily_report()
                    last_sent = key
                except Exception as e:
                    log.error(f"report: {e}")
        except Exception as e:
            log.error(f"loop: {e}")
        time.sleep(60)

if __name__ == "__main__":
    main()
