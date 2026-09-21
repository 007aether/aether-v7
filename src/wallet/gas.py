"""AETHER v7.3 — Gas tracker"""
import json
from .chains import CHAINS, gas_price_gwei
from ..utils import setup_logger

log = setup_logger("gas")

def all_gas():
    out = {}
    for chain in CHAINS:
        if chain == "solana":
            continue
        g = gas_price_gwei(chain)
        out[chain] = {
            "name": CHAINS[chain]["name"],
            "gas_gwei": g,
            "symbol": CHAINS[chain]["symbol"],
        }
    return out

def cheapest(n=3):
    """أرخص n شبكات للـ gas"""
    data = all_gas()
    valid = [(k, v) for k, v in data.items() if v["gas_gwei"] is not None]
    valid.sort(key=lambda x: x[1]["gas_gwei"])
    return [{"chain": k, **v} for k, v in valid[:n]]

if __name__ == "__main__":
    print(json.dumps({
        "all": all_gas(),
        "cheapest": cheapest(),
    }, indent=2, ensure_ascii=False))
