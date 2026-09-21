"""AETHER v7 — Wallet manager (seeds + PKs, local only)
⚠️ الـ seeds عمرها ما كاتخرج من الجهاز. غير العناوين كاتحسب."""
import json
from ..config import ROOT
from ..utils import setup_logger

log = setup_logger("wallet")

try:
    from web3 import Web3
    from eth_account import Account
    from eth_account.hdaccount import generate_mnemonic, key_from_seed
    Account.enable_unaudited_hdwallet_features()
    WEB3_OK = True
except ImportError:
    WEB3_OK = False
    log.warning("web3 not installed")

SECRETS = ROOT / ".wallet_secrets.json"
# مسارات مشتقة معيارية (Ethereum/Solana)
ETH_DERIV_PATH = "m/44'/60'/0'/0/0"

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
    """يشتق عنوان ETH من seed phrase (محلياً فقط)"""
    if not WEB3_OK:
        return None
    try:
        path = f"m/44'/60'/0'/0/{index}"
        acct = Account.from_mnemonic(seed_phrase, account_path=path)
        return acct.address
    except Exception as e:
        log.error(f"eth derive: {e}")
        return None

def eth_address_from_pk(pk):
    if not WEB3_OK:
        return None
    try:
        if not isinstance(pk, str) or not pk.startswith("0x"):
            return None
        return Account.from_key(pk).address
    except Exception as e:
        log.error(f"pk: {e}")
        return None

def check_eth_balance(address, rpc="https://ethereum.publicnode.com"):
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
    if not WEB3_OK:
        return {"error": "web3 not installed"}
    secrets = load_secrets()
    wallets = {}

    # 1. metamask_seed → ETH address
    mm = secrets.get("metamask_seed")
    if isinstance(mm, str) and len(mm.split()) >= 12:
        addr = eth_address_from_seed(mm)
        if addr:
            entry = {"type": "eth", "source": "metamask_seed", "address": addr}
            if include_balance:
                entry["eth"] = check_eth_balance(addr)
            wallets["metamask"] = entry

    # 2. phantom_seed → (Solana — محتاج مكتبة أخرى، ندير placeholder)
    ph = secrets.get("phantom_seed")
    if isinstance(ph, str) and len(ph.split()) >= 12:
        wallets["phantom"] = {
            "type": "solana",
            "source": "phantom_seed",
            "note": "Solana derivation يحتاج مكتبة solana (سنضيفها لاحقاً)",
        }

    # 3. أي private keys إضافية
    for key, val in secrets.items():
        if key in ("metamask_seed", "phantom_seed", "telegram", "bot_token",
                   "packetstream_cid", "saved_at"):
            continue
        if isinstance(val, str) and val.startswith("0x") and len(val) >= 64:
            addr = eth_address_from_pk(val)
            if addr:
                entry = {"type": "eth", "source": key, "address": addr}
                if include_balance:
                    entry["eth"] = check_eth_balance(addr)
                wallets[key] = entry

    return {"count": len(wallets), "wallets": wallets}

if __name__ == "__main__":
    import json as j
    print(j.dumps(summary(), indent=2, ensure_ascii=False))
