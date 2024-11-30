import binascii
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import json

from interface import ClassInterface


class TransactionInput(ClassInterface):
    def __init__(self, transaction_hash: str, output_index: int, public_key: str = "", signature: str = ""):
        self.transaction_hash = transaction_hash
        self.output_index = output_index
        self.public_key = public_key
        self.signature = signature

    def sign_transaction_input(self, private_key_object):
        # Hash the input UTXO data
        input_data = json.dumps(
            self.transaction_hash, sort_keys=True).encode('utf-8')
        hashed_data = SHA256.new(input_data)

        # Sign the hash
        signature = pkcs1_15.new(private_key_object).sign(hashed_data)

        # Return the signature (hex-encoded)
        return signature.hex()

    def validate_transaction_input(self, public_key, signature):
        try:
            # Hash the input UTXO data
            input_data = json.dumps(
                self.transaction_hash, sort_keys=True).encode('utf-8')
            hashed_data = SHA256.new(input_data)

            # Load the public key
            public_key_object = RSA.import_key(public_key)

            # Decode the hex-encoded signature
            signature_bytes = binascii.unhexlify(signature)

            # Verify the signature
            pkcs1_15.new(public_key_object).verify(
                hashed_data, signature_bytes)
            return True  # If no exception is raised, the signature is valid
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
