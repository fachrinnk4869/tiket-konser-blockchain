import json


class TransactionOutput:
    def __init__(self, public_key_hash: str, amount: int, ticket=None):
        self.amount = amount
        self.public_key_hash = public_key_hash
        self.ticket = ticket

    def to_json(self):
        return json.dumps({
            "amount": self.amount,
            "public_key_hash": self.public_key_hash,
            "ticket": self.ticket,
        })

    def to_dict(self):
        return {
            "amount": self.amount,
            "public_key_hash": self.public_key_hash,
            "ticket": self.ticket,
        }

    @staticmethod
    def from_dict(data):
        # Convert a dictionary back into a TransactionOutput object
        return TransactionOutput(
            public_key_hash=data['public_key_hash'],
            amount=data['amount'],
            ticket=data.get("ticket"),
        )
