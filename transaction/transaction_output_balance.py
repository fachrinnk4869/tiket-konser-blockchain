import json

from interface import ClassInterface


class TransactionOutputBalance(ClassInterface):
    def __init__(self, public_key_hash: str, amount=None, type=None):
        self.public_key_hash = public_key_hash
        self.amount = amount
        self.type = "balance"

    def to_json(self):
        return json.dumps({
            "public_key_hash": self.public_key_hash,
            "amount": self.amount,
            "type": self.type,
        })

    def to_dict(self):
        return {
            "public_key_hash": self.public_key_hash,
            "amount": self.amount,
            "type": self.type,
        }

    @classmethod
    def to_class(cls, data):
        return cls(
            public_key_hash=data['public_key_hash'],
            amount=data.get("amount"),
        )
