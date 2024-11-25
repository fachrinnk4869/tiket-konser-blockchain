import json
import binascii
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15

from transaction.transaction_input import TransactionInput
from transaction.transaction_output import TransactionOutput


class Owner:
    def __init__(self, public_key_hex: str, private_key):
        self.public_key_hex = public_key_hex
        self.private_key = private_key

    def to_json(self) -> str:
        # Serialize private_key to PEM format string
        private_key_pem = self.private_key.export_key().decode(
            'utf-8')  # Convert to PEM string

        return json.dumps({
            "public_key_hex": self.public_key_hex,
            "private_key": private_key_pem  # Serialize private key to PEM format
        })

    def to_dict(self):
        # Only serialize public_key_hex for the owner (private_key remains private)
        return {
            "public_key_hex": self.public_key_hex
        }


class Transaction:
    def __init__(self, owner, inputs: [TransactionInput], outputs: [TransactionOutput], tx_id=0):
        self.owner = owner
        self.inputs = inputs
        self.outputs = outputs
        self.tx_id = tx_id  # Generate tx_id based on transaction data

    def generate_tx_id(self):
        """Generate a unique transaction ID based on the transaction's inputs and outputs."""
        transaction_data = {
            "inputs": [tx_input.to_json(with_signature_and_public_key=False) for tx_input in self.inputs],
            "outputs": [tx_output.to_json() for tx_output in self.outputs]
        }
        transaction_bytes = json.dumps(
            transaction_data, indent=2).encode('utf-8')
        # Generate tx_id as the hash of the transaction data
        return SHA256.new(transaction_bytes).hexdigest()

    def sign_transaction_data(self):
        transaction_dict = {
            "inputs": [tx_input.to_json(with_signature_and_public_key=False) for tx_input in self.inputs],
            "outputs": [tx_output.to_json() for tx_output in self.outputs]
        }
        transaction_bytes = json.dumps(
            transaction_dict, indent=2).encode('utf-8')
        hash_object = SHA256.new(transaction_bytes)
        signature = pkcs1_15.new(self.owner.private_key).sign(hash_object)
        return signature

    def sign(self):
        signature_hex = binascii.hexlify(
            self.sign_transaction_data()).decode("utf-8")
        for transaction_input in self.inputs:
            transaction_input.signature = signature_hex
            transaction_input.public_key = self.owner.public_key_hex

    def to_json(self):
        return {
            "owner": self.owner.to_json(),
            "inputs": [i.to_json() for i in self.inputs],
            "outputs": [i.to_json() for i in self.outputs],
            "tx_id": self.tx_id  # Include tx_id in the data sent to nodes
        }

    def to_dict(self):
        return {
            "owner": self.owner.to_dict(),
            "inputs": [i.to_dict() for i in self.inputs],
            "outputs": [i.to_dict() for i in self.outputs],
            "tx_id": self.tx_id  # Include tx_id in the data sent to nodes
        }
