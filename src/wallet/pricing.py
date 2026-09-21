"""AETHER v7.4 — CoinGecko pricing (USD values)"""
import requests, json, time
from ..utils import setup_logger

log = setup_logger("pricing")

COINGECKO = "https://api.coingecko.com/api/v3/simple/price"

# symbol → coingecko id
SYMBOLS = {
    "ETH":  "ethereum",
    "SOL":  "solana",
    "POL":  "matic-network",
    "BNB":  "binancecoin",
    "BTC":  "bitcoin",
}

_cache = {"ts": 0, "data": {}}
CACHE_TTL = 120  # 2 دقائق

def get_prices(symbols=None):
    """يرجع dict: {symbol: usd_price}"""
    global _cache
    now = time.time()
    if now - _cache["ts"] < CACHE_TTL and _cache["data"]:
        return _cache["data"]
    syms = symbols or list(SYMBOLS.keys())
    ids = ",".join(SYMBOLS[s] for s in syms if s in SYMBOLS)
    try:
        r = requests.get(
            COINGECKO,
            params={"ids": ids, "vs_currencies": "usd"},
            timeout=15,
        )
        data = r.json()
        out = {}
        for sym in syms:
            cid = SYMBOLS.get(sym)
            if cid and cid in data:
                out[sym] = data[cid]["usd"]
        _cache = {"ts": now, "data": out}
        return out
    except Exception as e:
        log.error(f"coingecko: {e}")
        return _cache["data"] or {}

def usd_value(symbol, amount):
    if amount is None:
        return None
    p = get_prices().get(symbol)
    if p is None:
        return None
    return amount * p

if __name__ == "__main__":
    print(json.dumps(get_prices(), indent=2))
