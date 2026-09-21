"""AETHER v7 — Solana wallet (Phantom compatible)"""
import requests
from ..utils import setup_logger

log = setup_logger("solana")

try:
    from solders.keypair import Keypair
    SOLANA_OK = True
except ImportError:
    SOLANA_OK = False
    log.warning("solders not installed: pip install solders base58")

RPC = "https://api.mainnet-beta.solana.com"
LAMPORTS_PER_SOL = 1_000_000_000

def address_from_seed(seed_phrase, passphrase=""):
    """يشتق عنوان Solana من seed phrase (Phantom compatible)"""
    if not SOLANA_OK:
        return None
    try:
        kp = Keypair.from_seed_phrase_and_passphrase(seed_phrase.strip(), passphrase)
        return str(kp.pubkey())
    except Exception as e:
        log.error(f"derive: {e}")
        return None

def check_balance(address, rpc=RPC):
    """يرجع رصيد SOL"""
    try:
        r = requests.post(
            rpc,
            json={"jsonrpc": "2.0", "id": 1, "method": "getBalance",
                  "params": [address]},
            timeout=15,
        )
        data = r.json()
        if "result" in data:
            lamports = data["result"]["value"]
            return lamports / LAMPORTS_PER_SOL
    except Exception as e:
        log.debug(f"balance: {e}")
    return None

if __name__ == "__main__":
    import json
    from ..config import ROOT
    sec = ROOT / ".wallet_secrets.json"
    if sec.exists():
        data = json.loads(sec.read_text())
        seed = data.get("phantom_seed")
        if seed:
            addr = address_from_seed(seed)
            bal = check_balance(addr) if addr else None
            print(json.dumps({"address": addr, "sol": bal}, indent=2))
        else:
            print("no phantom_seed")
