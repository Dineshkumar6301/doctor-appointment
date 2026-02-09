import hashlib
from blockchain.web3_config import w3
from blockchain.contract import contract


def store_appointment_hash(appointment):
    """
    Store appointment notes hash on blockchain
    """
    if not appointment.appointment_notes:
        return None

    raw_text = f"{appointment.id}|{appointment.appointment_notes}|{appointment.doctor.id}"
    record_hash = hashlib.sha256(raw_text.encode()).hexdigest()

    tx = contract.functions.addRecord(
        record_hash,
        f"APT-{appointment.id}"
    ).transact({
        "from": w3.eth.accounts[0]
    })

    w3.eth.wait_for_transaction_receipt(tx)
    return record_hash
