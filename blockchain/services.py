from .web3_config import w3, contract

def add_record(file_hash, doctor_id):
    account = w3.eth.accounts[0]

    tx = contract.functions.addRecord(
        file_hash,
        doctor_id
    ).transact({
        "from": account
    })

    receipt = w3.eth.wait_for_transaction_receipt(tx)
    return receipt.transactionHash.hex()


import hashlib
from .web3_config import w3, contract

def generate_file_hash(appointment):
    raw = f"{appointment.id}|{appointment.patient_id}|{appointment.doctor_id}"
    return hashlib.sha256(raw.encode()).hexdigest()
