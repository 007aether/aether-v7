"""AETHER v7.3 — Real airdrop eligibility (with L2 support)"""
import json
from ..config import ROOT
from ..wallet.manager import eth_address_from_seed
from ..wallet import solana as sol
from ..wallet.chains import native_balance, tx_count, CHAINS
from ..utils import setup_logger

log = setup_logger("eligibility")

SECRETS = ROOT / ".wallet_secrets.json"

def _load():
    if not SECRETS.exists():
        return {}
    try:
        return json.loads(SECRETS.read_text())
    except Exception:
        return {}

def get_addresses():
    d = _load()
    eth = eth_address_from_seed(d.get("metamask_seed", "")) if d.get("metamask_seed") else None
    sol_addr = sol.address_from_seed(d.get("phantom_seed", "")) if d.get("phantom_seed") else None
    return eth, sol_addr

# قواعد الـ airdrops (heuristic)
RULES = {
    "Linea": {
        "chain": "linea", "need_tx": 5, "need_eth": 0.001,
        "note": "activity on Linea network",
    },
    "Scroll": {
        "chain": "scroll", "need_tx": 3, "need_eth": 0.001,
        "note": "bridged to Scroll",
    },
    "zkSync": {
        "chain": "zksync", "need_tx": 3, "need_eth": 0.001,
        "note": "activity on zkSync Era",
    },
    "Base": {
        "chain": "base", "need_tx": 5, "need_eth": 0.001,
        "note": "activity on Base",
    },
    "Arbitrum": {
        "chain": "arbitrum", "need_tx": 5, "need_eth": 0.001,
        "note": "activity on Arbitrum One",
    },
    "Optimism": {
        "chain": "optimism", "need_tx": 5, "need_eth": 0.001,
        "note": "activity on OP Mainnet",
    },
    "EigenLayer": {
        "chain": "ethereum", "need_tx": 5, "need_eth": 0.05,
        "note": "restaked ETH",
    },
    "Ethena": {
        "chain": "ethereum", "need_tx": 3, "need_eth": 0.01,
        "note": "held sUSDe/USDe",
    },
    "Hyperliquid": {
        "chain": "arbitrum", "need_tx": 10, "need_eth": 0.001,
        "note": "traded on Hyperliquid",
    },
    "Monad": {
        "chain": None, "need_tx": None, "need_eth": None,
        "note": "testnet — check https://testnet.monad.xyz",
    },
    "MegaETH": {
        "chain": None, "need_tx": None, "need_eth": None,
        "note": "testnet — check https://testnet.megaeth.com",
    },
}

def check_eligibility():
    eth_addr, sol_addr = get_addresses()
    if not eth_addr:
        return {"error": "no eth address"}

    # cache balances
    bal_cache = {}
    tx_cache = {}
    for chain in CHAINS:
        if chain == "solana":
            continue
        bal_cache[chain] = native_balance(chain, eth_addr)
        tx_cache[chain] = tx_count(chain, eth_addr)

    results = []
    for name, rule in RULES.items():
        chain = rule["chain"]
        if chain is None:
            results.append({
                "name": name, "chain": "?", "eligible": False,
                "reason": rule["note"], "balance": None, "tx_count": None,
            })
            continue

        bal = bal_cache.get(chain)
        tx = tx_cache.get(chain)
        eligible = False
        reason = ""

        if bal is None or tx is None:
            reason = f"RPC {chain} غير متاح"
        elif bal >= rule["need_eth"] and tx >= rule["need_tx"]:
            eligible = True
            reason = f"✓ meets {rule['need_eth']} ETH + {rule['need_tx']} tx"
        else:
            reason = f"يحتاج {rule['need_eth']} ETH + {rule['need_tx']} tx (عندك {bal:.4f} ETH, {tx} tx)"

        results.append({
            "name": name, "chain": chain, "eligible": eligible,
            "reason": reason, "balance": bal, "tx_count": tx,
            "note": rule["note"],
        })

    return {
        "eth_address": eth_addr,
        "sol_address": sol_addr,
        "chains_checked": len([c for c in CHAINS if c != "solana"]),
        "eligible_count": sum(1 for r in results if r["eligible"]),
        "total": len(results),
        "airdrops": results,
    }

if __name__ == "__main__":
    print(json.dumps(check_eligibility(), indent=2, ensure_ascii=False))
