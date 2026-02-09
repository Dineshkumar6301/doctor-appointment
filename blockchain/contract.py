from blockchain.web3_config import w3
import json
import os

# Path to ABI file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ABI_PATH = os.path.join(BASE_DIR, "abi.json")

# Load ABI
with open(ABI_PATH) as abi_file:
    ABI = json.load(abi_file)

# Contract address (Sepolia)
CONTRACT_ADDRESS = w3.to_checksum_address(
    "0xC4C123456789ABCDEF"
)

# Create contract instance
contract = w3.eth.contract(
    address=CONTRACT_ADDRESS,
    abi=ABI
)
