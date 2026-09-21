"""AETHER v7.7 — Hyperliquid paper trading (no real money)"""
import json, requests, sqlite3, time
from datetime import datetime
from ..config import DB_PATH, LOGS
from ..utils import now, setup_logger

log = setup_logger("hl_paper")

HL_INFO = "https://api.hyperliquid.xyz/info"

def ensure_tables():
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS paper_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT, symbol TEXT, side TEXT, size REAL,
            entry_price REAL, exit_price REAL, pnl REAL,
            status TEXT DEFAULT 'open', strategy TEXT
        );
        CREATE TABLE IF NOT EXISTS paper_portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT, balance_usd REAL
        );
    """)
    c.commit()
    c.close()

def fetch_price(symbol):
    try:
        r = requests.post(HL_INFO, json={"type": "allMids"}, timeout=10)
        data = r.json()
        price = data.get(symbol)
        return float(price) if price else None
    except Exception as e:
        log.error(f"fetch_price {symbol}: {e}")
        return None

def open_paper_trade(symbol, side, size_usd, strategy="manual"):
    ensure_tables()
    price = fetch_price(symbol)
    if not price:
        return {"error": f"no price for {symbol}"}
    size = size_usd / price
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.execute(
        "INSERT INTO paper_trades (ts, symbol, side, size, entry_price, strategy) "
        "VALUES (?,?,?,?,?,?)",
        (now(), symbol, side, size, price, strategy),
    )
    c.commit()
    c.close()
    log.info(f"Paper {side} {symbol} @ ${price:,.2f}")
    return {"symbol": symbol, "side": side, "price": price,
            "size": size, "size_usd": size_usd}

def close_paper_trade(trade_id):
    ensure_tables()
    c = sqlite3.connect(DB_PATH, timeout=10)
    row = c.execute(
        "SELECT symbol, side, size, entry_price FROM paper_trades WHERE id=?",
        (trade_id,),
    ).fetchone()
    if not row:
        c.close()
        return {"error": "trade not found"}
    symbol, side, size, entry = row
    price = fetch_price(symbol)
    if not price:
        c.close()
        return {"error": "no price"}
    pnl = (price - entry) * size if side == "buy" else (entry - price) * size
    c.execute(
        "UPDATE paper_trades SET exit_price=?, pnl=?, status='closed' WHERE id=?",
        (price, pnl, trade_id),
    )
    c.commit()
    c.close()
    return {"trade_id": trade_id, "exit_price": price, "pnl": pnl}

def portfolio():
    ensure_tables()
    c = sqlite3.connect(DB_PATH, timeout=10)
    open_trades = c.execute(
        "SELECT id, symbol, side, size, entry_price FROM paper_trades WHERE status='open'"
    ).fetchall()
    closed = c.execute(
        "SELECT COUNT(*), COALESCE(SUM(pnl),0) FROM paper_trades WHERE status='closed'"
    ).fetchone()
    c.close()

    positions = []
    unrealized = 0
    for tid, sym, side, size, entry in open_trades:
        price = fetch_price(sym)
        if not price: continue
        pnl = (price - entry) * size if side == "buy" else (entry - price) * size
        unrealized += pnl
        positions.append({
            "id": tid, "symbol": sym, "side": side,
            "size": size, "entry": entry, "current": price, "pnl": pnl,
        })

    return {
        "open_trades": len(open_trades),
        "closed_trades": closed[0],
        "realized_pnl": closed[1],
        "unrealized_pnl": unrealized,
        "positions": positions,
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "portfolio":
            print(json.dumps(portfolio(), indent=2, ensure_ascii=False))
        elif cmd == "price":
            symbol = sys.argv[2] if len(sys.argv) > 2 else "BTC"
            p = fetch_price(symbol)
            print(f"{symbol}: ${p:,.2f}" if p else f"{symbol}: no price")
        elif cmd == "open":
            symbol = sys.argv[2] if len(sys.argv) > 2 else "BTC"
            side = sys.argv[3] if len(sys.argv) > 3 else "buy"
            size = float(sys.argv[4]) if len(sys.argv) > 4 else 100
            print(json.dumps(open_paper_trade(symbol, side, size), indent=2))
        elif cmd == "close":
            tid = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            print(json.dumps(close_paper_trade(tid), indent=2))
    else:
        print("Usage: {price|open|close|portfolio}")
