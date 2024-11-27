import json

from interface import ClassInterface


class TransactionInput(ClassInterface):
    def __init__(self, transaction_hash: str, output_index: int, public_key: str = "", signature: str = ""):
        self.transaction_hash = transaction_hash
        self.output_index = output_index
        self.public_key = public_key
        self.signature = signature

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
            output_index=data['ticket_id'],
            public_key=data['public_key_hash'],
            signature=data['signature'],
        )

    def to_dict(self):
        return {
            "transaction_hash": self.transaction_hash,
            "output_index": self.output_index,
            "public_key": self.public_key,
            "signature": self.signature
        }
