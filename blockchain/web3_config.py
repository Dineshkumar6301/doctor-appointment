from web3 import Web3
import json
import os

WEB3_PROVIDER = "https://bsc-testnet.publicnode.com"
w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))

CONTRACT_ADDRESS = Web3.to_checksum_address(
    "0xd2a5bC10698FD955D1Fe6cb468a17809A08fd005"
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE_DIR, "blockchain/hospital_abi.json")) as f:
    ABI = json.load(f)

contract = w3.eth.contract(
    address=CONTRACT_ADDRESS,
    abi=ABI
)
