import binascii
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import json

from eth_account.messages import encode_defunct
from web3 import Web3
from interface import ClassInterface
ganache_url = "http://127.0.0.1:8545"
web3 = Web3(Web3.HTTPProvider(ganache_url))


class TransactionInput(ClassInterface):
    def __init__(self, transaction_hash: str, output_index: int, public_key: str = "", signature: str = ""):
        self.transaction_hash = transaction_hash
        self.output_index = output_index
        self.public_key = public_key
        self.signature = signature

    def sign_transaction_input(self, private_key_object):
        # Hash the input UTXO data
        input_data = json.dumps(
            self.transaction_hash, sort_keys=True)
        encoded_message = encode_defunct(text=input_data)
        # Sign the encoded message with the private key
        signed_message = web3.eth.account.sign_message(
            encoded_message, private_key_object)
        print(f"Signed Message: {signed_message}")

        # Signature details
        signature = signed_message.signature.hex()

        # Return the signature (hex-encoded)
        return signature

    def validate_transaction_input(self, public_key, signature):
        try:
            # Hash the input UTXO data
            input_data = json.dumps(
                self.transaction_hash, sort_keys=True)
            encoded_message = encode_defunct(text=input_data)
            # Recover the address from the signature
            recovered_address = web3.eth.account.recover_message(
                encoded_message, signature=signature)
            print(f"Recovered Address: {recovered_address}")

            # Check if the recovered address matches the public address
            if recovered_address == public_key:
                print("Signature is valid! The signer owns the private key.")
                return True  # If no exception is raised, the signature is valid
            else:
                print("Signature is invalid!")
                return False  # Signature is invalid
        except (ValueError, TypeError):
            return False  # Signature is invalid

    def to_json(self, with_signature_and_public_key: bool = True):
        if with_signature_and_public_key:
            return json.dumps({
                "transaction_hash": self.transaction_hash,
                "output_index": self.output_index,
                "public_key": self.public_key,
                "signature": self.signature
            })
        else:
            return json.dumps({
                "transaction_hash": self.transaction_hash,
                "output_index": self.output_index
            })

    @classmethod
    def to_class(cls, data):
        return cls(
            transaction_hash=data['tx_id'],
            output_index=data['output_index'],
            public_key=data['public_key_hash'],
            signature=data['signature'],
        )

    @classmethod
    def to_class_without_sign(cls, data):
        return cls(
            transaction_hash=data['tx_id'],
            output_index=data['output_index'],
        )

    def to_dict(self):
        return {
            "transaction_hash": self.transaction_hash,
            "output_index": self.output_index,
            "public_key": self.public_key,
            "signature": self.signature
        }
