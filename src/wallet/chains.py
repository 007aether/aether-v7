"""AETHER v7.3 — Multi-chain RPC support"""
import requests
from ..utils import setup_logger

log = setup_logger("chains")

CHAINS = {
    "ethereum": {
        "name": "Ethereum", "rpc": "https://ethereum.publicnode.com",
        "symbol": "ETH", "explorer": "https://etherscan.io", "chain_id": 1,
    },
    "linea": {
        "name": "Linea", "rpc": "https://rpc.linea.build",
        "symbol": "ETH", "explorer": "https://lineascan.build", "chain_id": 59144,
    },
    "scroll": {
        "name": "Scroll", "rpc": "https://rpc.scroll.io",
        "symbol": "ETH", "explorer": "https://scrollscan.com", "chain_id": 534352,
    },
    "zksync": {
        "name": "zkSync Era", "rpc": "https://mainnet.era.zksync.io",
        "symbol": "ETH", "explorer": "https://explorer.zksync.io", "chain_id": 324,
    },
    "base": {
        "name": "Base", "rpc": "https://mainnet.base.org",
        "symbol": "ETH", "explorer": "https://basescan.org", "chain_id": 8453,
    },
    "arbitrum": {
        "name": "Arbitrum One", "rpc": "https://arb1.arbitrum.io/rpc",
        "symbol": "ETH", "explorer": "https://arbiscan.io", "chain_id": 42161,
    },
    "optimism": {
        "name": "Optimism", "rpc": "https://mainnet.optimism.io",
        "symbol": "ETH", "explorer": "https://optimistic.etherscan.io", "chain_id": 10,
    },
    "polygon": {
        "name": "Polygon", "rpc": "https://polygon-rpc.com",
        "symbol": "POL", "explorer": "https://polygonscan.com", "chain_id": 137,
    },
    "solana": {
        "name": "Solana", "rpc": "https://api.mainnet-beta.solana.com",
        "symbol": "SOL", "explorer": "https://solscan.io", "chain_id": None,
    },
}

def rpc_call(chain, method, params=None):
    info = CHAINS.get(chain)
    if not info:
        return None
    try:
        r = requests.post(
            info["rpc"],
            json={"jsonrpc": "2.0", "id": 1, "method": method,
                  "params": params or []},
            timeout=15,
        )
        return r.json().get("result")
    except Exception as e:
        log.debug(f"{chain}.{method}: {e}")
        return None

def native_balance(chain, address):
    if chain == "solana":
        r = rpc_call(chain, "getBalance", [address])
        if r and isinstance(r, dict):
            return r.get("value", 0) / 1_000_000_000
        return None
    r = rpc_call(chain, "eth_getBalance", [address, "latest"])
    if r is None:
        return None
    try:
        return int(r, 16) / 1e18
    except Exception:
        return None

def tx_count(chain, address):
    if chain == "solana":
        return None
    r = rpc_call(chain, "eth_getTransactionCount", [address, "latest"])
    if r is None:
        return None
    try:
        return int(r, 16)
    except Exception:
        return None

def gas_price_gwei(chain):
    if chain == "solana":
        return None
    r = rpc_call(chain, "eth_gasPrice", [])
    if r is None:
        return None
    try:
        return int(r, 16) / 1e9
    except Exception:
        return None

def check_all_chains(address_eth, address_sol=None):
    """فحص كل السلاسل لعنوان معين"""
    out = {}
    for chain in CHAINS:
        if chain == "solana":
            if not address_sol:
                continue
            bal = native_balance(chain, address_sol)
            out[chain] = {
                "balance": bal, "symbol": "SOL",
                "tx_count": None, "gas_gwei": None,
            }
        else:
            bal = native_balance(chain, address_eth)
            tx = tx_count(chain, address_eth)
            gas = gas_price_gwei(chain)
            out[chain] = {
                "balance": bal, "symbol": CHAINS[chain]["symbol"],
                "tx_count": tx, "gas_gwei": gas,
            }
    return out

if __name__ == "__main__":
    import json
    from ..config import ROOT
    from ..wallet.manager import eth_address_from_seed
    from ..wallet import solana as sol

    sec = ROOT / ".wallet_secrets.json"
    if not sec.exists():
        print("no secrets")
        raise SystemExit(1)
    data = json.loads(sec.read_text())
    eth = eth_address_from_seed(data.get("metamask_seed", "")) if data.get("metamask_seed") else None
    sol_addr = sol.address_from_seed(data.get("phantom_seed", "")) if data.get("phantom_seed") else None
    print(json.dumps(check_all_chains(eth, sol_addr), indent=2, ensure_ascii=False))
