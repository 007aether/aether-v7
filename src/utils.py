"""AETHER v7 — Utils"""
import logging, sys
from datetime import datetime
from .config import LOGS

def setup_logger(name):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")
    fh = logging.FileHandler(LOGS / f"{name}.log")
    fh.setFormatter(fmt)
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

def now():
    return datetime.now().isoformat()

def ts_human():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
