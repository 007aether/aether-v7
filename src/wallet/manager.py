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
from . import pricing

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
    """Multi-chain portfolio with USD values"""
    secrets = load_secrets()
    wallets = {}
    total_usd = 0.0

    # ETH wallets (metamask + any 0x keys)
    mm = secrets.get("metamask_seed")
    if isinstance(mm, str) and len(mm.split()) >= 12:
        addr = eth_address_from_seed(mm)
        if addr:
            bal = eth_balance(addr) if include_balance else None
            usd = pricing.usd_value("ETH", bal) if bal is not None else None
            wallets["metamask_eth"] = {
                "chain": "ethereum", "source": "metamask_seed",
                "address": addr, "balance": bal, "symbol": "ETH",
                "usd": usd,
            }
            if usd: total_usd += usd

    # SOL wallet
    ph = secrets.get("phantom_seed")
    if isinstance(ph, str) and len(ph.split()) >= 12:
        addr = sol.address_from_seed(ph)
        if addr:
            bal = sol.check_balance(addr) if include_balance else None
            usd = pricing.usd_value("SOL", bal) if bal is not None else None
            wallets["phantom_sol"] = {
                "chain": "solana", "source": "phantom_seed",
                "address": addr, "balance": bal, "symbol": "SOL",
                "usd": usd,
            }
            if usd: total_usd += usd

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
                bal = eth_balance(addr) if include_balance else None
                usd = pricing.usd_value("ETH", bal) if bal is not None else None
                wallets[f"{key}_eth"] = {
                    "chain": "ethereum", "source": key,
                    "address": addr, "balance": bal, "symbol": "ETH",
                    "usd": usd,
                }
                if usd: total_usd += usd

    return {
        "count": len(wallets),
        "total_usd": round(total_usd, 2),
        "wallets": wallets,
    }


if __name__ == "__main__":
    print(json.dumps(summary(), indent=2, ensure_ascii=False))
