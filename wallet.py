import json
import binascii
import logging
from flask import session

from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
from Crypto.PublicKey import RSA

from interface import ClassInterface
from transaction.transaction_input import TransactionInput
from transaction.transaction_output_balance import TransactionOutputBalance
from transaction.transaction_output_ticket import TransactionOutputTicket


class Owner:
    @staticmethod
    def get_public_key(owner):
        logging.warning(f"halo {owner}")
        with open(f'./keys/public_{owner}.pem', 'r') as file:
            return file.read()

    @staticmethod
    def get_private_key(owner):
        logging.warning(f"halo {owner}")
        with open(f'./keys/private_{owner}.pem', 'r') as file:
            private_key_pem = file.read()
            # Convert the PEM string to an RSA key object
            private_key = RSA.import_key(private_key_pem)
            return private_key


class Transaction(ClassInterface):
    def __init__(self, owner, inputs: [TransactionInput], outputs: [TransactionOutputTicket], owner_id=None, tx_id=0):
        self.owner = owner
        self.inputs = inputs
        self.outputs = outputs
        self.tx_id = tx_id  # Generate tx_id based on transaction data
        self.owner_id = owner_id

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
        signature = pkcs1_15.new(Owner.get_private_key(
            self.owner_id)).sign(hash_object)
        return signature

    def sign(self):
        signature_hex = binascii.hexlify(
            self.sign_transaction_data()).decode("utf-8")
        for transaction_input in self.inputs:
            transaction_input.signature = signature_hex
            transaction_input.public_key = self.owner

    def to_json(self):
        return {
            "owner": self.owner,
            "inputs": [i.to_json() for i in self.inputs],
            "outputs": [i.to_json() for i in self.outputs],
            "tx_id": self.tx_id  # Include tx_id in the data sent to nodes
        }

    def to_dict(self):
        return {
            "owner": self.owner,
            "inputs": [i.to_dict() for i in self.inputs],
            "outputs": [i.to_dict() for i in self.outputs],
            "tx_id": self.tx_id  # Include tx_id in the data sent to nodes
        }

    @classmethod
    def to_class(cls, data):
        logging.warning(f"hai {data['outputs']}")
        return cls(
            owner=data['owner'],
            inputs=[TransactionInput(**input_data)
                    for input_data in data["inputs"]],
            outputs=[
                TransactionOutputTicket(**output_data)
                if output_data['type'] == "ticket"
                else TransactionOutputBalance(**output_data)
                for output_data in data["outputs"]
            ],
            tx_id=data["tx_id"]
        )
