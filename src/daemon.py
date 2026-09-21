"""AETHER v7 — OODA Daemon"""
import time
from .brain import think, log_event
from .utils import setup_logger

log = setup_logger("daemon")

def main():
    log.info("=" * 60)
    log.info("AETHER v7 DAEMON START")
    log.info("=" * 60)
    log_event("INFO", "daemon", "daemon started")
    while True:
        try:
            think("فحص النظام: DB قائم، ollama متصل.")
        except KeyboardInterrupt:
            log.info("Interrupted, exiting")
            break
        except Exception as e:
            log.error(f"loop error: {e}")
        time.sleep(60)

if __name__ == "__main__":
    main()
