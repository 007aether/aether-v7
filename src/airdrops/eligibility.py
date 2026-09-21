"""AETHER v7.2 — Airdrop eligibility checker"""
import requests, json
from ..config import ROOT
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

def get_eth_address():
    """يرجع عنوان ETH الأساسي"""
    try:
        from ..wallet.manager import eth_address_from_seed
        seed = _load().get("metamask_seed")
        if seed:
            return eth_address_from_seed(seed)
    except Exception as e:
        log.error(f"eth addr: {e}")
    return None

def tx_count_eth(address, rpc="https://ethereum.publicnode.com"):
    """شحال من transaction دار"""
    try:
        r = requests.post(
            rpc,
            json={"jsonrpc": "2.0", "id": 1, "method": "eth_getTransactionCount",
                  "params": [address, "latest"]},
            timeout=10,
        )
        return int(r.json()["result"], 16)
    except Exception as e:
        log.debug(f"tx count: {e}")
        return None

def eth_balance(address, rpc="https://ethereum.publicnode.com"):
    try:
        r = requests.post(
            rpc,
            json={"jsonrpc": "2.0", "id": 1, "method": "eth_getBalance",
                  "params": [address, "latest"]},
            timeout=10,
        )
        return int(r.json()["result"], 16) / 1e18
    except Exception:
        return None

# Airdrop eligibility rules (heuristics)
RULES = {
    "Linea": {
        "chain": "linea",
        "need_tx": 5,
        "need_eth": 0.01,
        "note": "activity on Linea network",
    },
    "Scroll": {
        "chain": "scroll",
        "need_tx": 3,
        "need_eth": 0.005,
        "note": "bridged to Scroll",
    },
    "zkSync": {
        "chain": "zksync",
        "need_tx": 3,
        "need_eth": 0.005,
        "note": "activity on zkSync Era",
    },
    "EigenLayer": {
        "chain": "ethereum",
        "need_tx": 5,
        "need_eth": 0.05,
        "note": "restaked ETH",
    },
    "Ethena": {
        "chain": "ethereum",
        "need_tx": 3,
        "need_eth": 0.01,
        "note": "held sUSDe/USDe",
    },
    "Hyperliquid": {
        "chain": "hyperliquid",
        "need_tx": 10,
        "need_eth": 0.0,
        "note": "traded on Hyperliquid",
    },
}

def check_eligibility():
    addr = get_eth_address()
    if not addr:
        return {"error": "no eth address"}

    eth_bal = eth_balance(addr)
    eth_tx = tx_count_eth(addr)

    results = []
    for name, rule in RULES.items():
        eligible = False
        reason = ""
        if rule["chain"] == "ethereum":
            if eth_bal is not None and eth_tx is not None:
                if eth_bal >= rule["need_eth"] and eth_tx >= rule["need_tx"]:
                    eligible = True
                    reason = "meets threshold"
                else:
                    reason = f"needs {rule['need_eth']} ETH + {rule['need_tx']} tx"
        else:
            reason = f"check on {rule['chain']} (L2 support soon)"
        results.append({
            "name": name,
            "chain": rule["chain"],
            "eligible": eligible,
            "reason": reason,
            "note": rule["note"],
        })

    return {
        "address": addr,
        "eth_balance": eth_bal,
        "eth_tx_count": eth_tx,
        "airdrops": results,
    }

if __name__ == "__main__":
    print(json.dumps(check_eligibility(), indent=2, ensure_ascii=False))
