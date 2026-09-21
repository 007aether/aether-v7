"""AETHER v7.2 — Multi-chain wallet manager (ETH + SOL)"""
import json
from ..config import ROOT
from ..utils import setup_logger

log = setup_logger("wallet")

try:
    from web3 import Web3
    from eth_account import Account
    Account.enable_unaudited_hdwallet_features()
    WEB3_OK = True
except ImportError:
    WEB3_OK = False

from . import solana as sol

SECRETS = ROOT / ".wallet_secrets.json"
ETH_RPC = "https://ethereum.publicnode.com"

def load_secrets():
    if not SECRETS.exists():
        return {}
    try:
        data = json.loads(SECRETS.read_text())
        return data if isinstance(data, dict) else {}
    except Exception as e:
        log.error(f"load: {e}")
        return {}

def eth_address_from_seed(seed_phrase, index=0):
    if not WEB3_OK:
        return None
    try:
        path = f"m/44'/60'/0'/0/{index}"
        return Account.from_mnemonic(seed_phrase, account_path=path).address
    except Exception as e:
        log.error(f"eth derive: {e}")
        return None

def eth_balance(address, rpc=ETH_RPC):
    if not WEB3_OK:
        return None
    try:
        w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
        if not w3.is_connected():
            return None
        return w3.eth.get_balance(Web3.to_checksum_address(address)) / 1e18
    except Exception as e:
        log.debug(f"eth: {e}")
        return None

def summary(include_balance=True):
    secrets = load_secrets()
    wallets = {}

    # ETH from metamask_seed
    mm = secrets.get("metamask_seed")
    if isinstance(mm, str) and len(mm.split()) >= 12:
        addr = eth_address_from_seed(mm)
        if addr:
            wallets["metamask_eth"] = {
                "chain": "ethereum",
                "source": "metamask_seed",
                "address": addr,
                "balance": eth_balance(addr) if include_balance else None,
                "symbol": "ETH",
            }

    # SOL from phantom_seed
    ph = secrets.get("phantom_seed")
    if isinstance(ph, str) and len(ph.split()) >= 12:
        addr = sol.address_from_seed(ph)
        if addr:
            wallets["phantom_sol"] = {
                "chain": "solana",
                "source": "phantom_seed",
                "address": addr,
                "balance": sol.check_balance(addr) if include_balance else None,
                "symbol": "SOL",
            }

    # Additional PKs
    skip = {"metamask_seed", "phantom_seed", "telegram", "bot_token",
            "packetstream_cid", "saved_at", "okx_address"}
    for key, val in secrets.items():
        if key in skip:
            continue
        if isinstance(val, str) and val.startswith("0x") and len(val) >= 64:
            addr = None
            if WEB3_OK:
                try:
                    addr = Account.from_key(val).address
                except Exception:
                    pass
            if addr:
                wallets[f"{key}_eth"] = {
                    "chain": "ethereum",
                    "source": key,
                    "address": addr,
                    "balance": eth_balance(addr) if include_balance else None,
                    "symbol": "ETH",
                }

    return {"count": len(wallets), "wallets": wallets}

if __name__ == "__main__":
    print(json.dumps(summary(), indent=2, ensure_ascii=False))
