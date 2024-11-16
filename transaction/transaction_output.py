import json


class TransactionOutput:
    def __init__(self, public_key_hash: str, amount: int, seat=None, event=None):
        self.amount = amount
        self.public_key_hash = public_key_hash
        self.seat = seat
        self.event = event

    def to_json(self):
        return json.dumps({
            "amount": self.amount,
            "public_key_hash": self.public_key_hash,
            "seat": self.seat,
            "event": self.event
        })

    def to_dict(self):
        return {
            "amount": self.amount,
            "public_key_hash": self.public_key_hash,
            "seat": self.seat,
            "event": self.event,
        }

    @staticmethod
    def from_dict(data):
        # Convert a dictionary back into a TransactionOutput object
        return TransactionOutput(
            public_key_hash=data['public_key_hash'],
            amount=data['amount'],
            seat=data.get("seat"),
            event=data.get("event"),
        )
