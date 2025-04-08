import os
import time
import logging
import random

import requests
from web3 import Web3
from web3.providers import HTTPProvider
from dotenv import load_dotenv

load_dotenv()

# =============================================
# Account configuration
# =============================================
ACCOUNTS = [
    {
        "private_key": os.getenv("WALLET1_KEY"),
        "proxy": "http://user:pass@ip:port",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    },
    {
        "private_key": os.getenv("WALLET2_KEY"),
        "proxy": "http://user:pass@ip:port",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..."
    }
    #if you need more accs add fields in the same format
]

COMMON_CONFIG = {
    "contract_address": Web3.to_checksum_address("0xa18f6FCB2Fd4884436d10610E69DB7BFa1bFe8C7"),
    "rpc_url": "https://rpc.testnet.humanity.org/",
    "chain_id": 1942999413,
    "gas_limit": "0x59fdc",
    "gas_price": "0x0",
    "timeout": 120
}

# =============================================
# Logs settings
# =============================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("multi_transaction.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================
# Proxy settings
# =============================================
def get_w3(proxy_config, user_agent):
    session = requests.Session()
    session.proxies = {"https": proxy_config, "http": proxy_config}
    session.headers.update({"User-Agent": user_agent})

    provider = HTTPProvider(COMMON_CONFIG["rpc_url"], session=session)
    w3 = Web3(provider)

    if not w3.is_connected():
        raise ConnectionError("RPC connection failed")
    return w3

# =============================================
# Main function for single acc
# =============================================
def process_account(account_data):
    try:
        account_address = Web3().eth.account.from_key(account_data["private_key"]).address
        short_address = f"{account_address[:6]}...{account_address[-4:]}"

        w3 = get_w3(account_data["proxy"], account_data["user_agent"])
        account = w3.eth.account.from_key(account_data["private_key"])
        logger.info(f"[{short_address}] Processing account")


        nonce = w3.eth.get_transaction_count(account.address)
        tx = {
            "chainId": COMMON_CONFIG["chain_id"],
            "from": account.address,
            "to": COMMON_CONFIG["contract_address"],
            "data": "0xb88a802f",
            "gas": COMMON_CONFIG["gas_limit"],
            "gasPrice": COMMON_CONFIG["gas_price"],
            "nonce": nonce,
        }


        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        logger.info(f"[{short_address}] Transaction sent: 0x{tx_hash.hex()}")


        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=COMMON_CONFIG["timeout"])
        status = "SUCCESS" if receipt.status == 1 else "FAILED"

        logger.info(f"[{short_address}] Transaction {status}")

        return True

    except Exception as e:
        logger.error(f"[{short_address}] Error: {str(e)}", exc_info=True)
        return False

# =============================================
# Start for all accs
# =============================================
if __name__ == "__main__":
    logger.info("=== START MULTI-ACCOUNT PROCESSING ===")

    total_success = 0
    total_errors = 0

    for idx, acc in enumerate(ACCOUNTS):
        start_time = time.time()
        logger.info(f"Processing account {idx+1}/{len(ACCOUNTS)}")

        result = process_account(acc)

        if result:
            total_success += 1
        else:
            total_errors += 1

        sleep = random.randint(10, 30)
        logger.info(f"Waiting {sleep} seconds before next account")
        time.sleep(sleep)

    logger.info(f"=== COMPLETED ===")
    logger.info(f"Success: {total_success} | Errors: {total_errors}")
