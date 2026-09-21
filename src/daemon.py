"""AETHER v7 — Unified daemon (brain + sync + learn + airdrops)"""
import time
from .brain import think, log_event
from .utils import setup_logger

log = setup_logger("daemon")

CYCLE_SECS   = 60          # brain cycle
SYNC_SECS    = 15 * 60     # earnings + airdrops (15min)
LEARN_SECS   = 30 * 60     # learning analysis (30min)

def _try(label, fn):
    try:
        result = fn()
        log.info(f"{label}: OK")
        return result
    except Exception as e:
        log.error(f"{label}: {e}")
        return None

def main():
    log.info("=" * 60)
    log.info("AETHER v7 DAEMON START")
    log.info("=" * 60)
    log_event("INFO", "daemon", "daemon started")

    last_sync = 0
    last_learn = 0

    while True:
        try:
            # 1. Brain cycle
            think("فحص النظام: DB قائم، ollama متصل.")

            now_ts = time.time()

            # 2. Sync earnings + airdrops
            if now_ts - last_sync > SYNC_SECS:
                from .earnings.sync import sync
                from .airdrops.tracker import refresh
                _try("sync", sync)
                _try("airdrops", refresh)
                last_sync = now_ts

            # 3. Learning
            if now_ts - last_learn > LEARN_SECS:
                from .learning.analyzer import analyze_cycles
                _try("learn", analyze_cycles)
                last_learn = now_ts

        except KeyboardInterrupt:
            log.info("Interrupted")
            break
        except Exception as e:
            log.error(f"loop: {e}")

        time.sleep(CYCLE_SECS)

if __name__ == "__main__":
    main()
