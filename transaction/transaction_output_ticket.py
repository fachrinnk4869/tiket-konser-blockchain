import json

from interface import ClassInterface


class TransactionOutputTicket(ClassInterface):
    def __init__(self, public_key_hash: str, ticket=None, type=None):
        self.public_key_hash = public_key_hash
        self.ticket = ticket
        self.type = "ticket"

    def to_json(self):
        return json.dumps({
            "public_key_hash": self.public_key_hash,
            "ticket": self.ticket,
            "type": self.type,
        })

    def to_dict(self):
        return {
            "public_key_hash": self.public_key_hash,
            "ticket": self.ticket,
            "type": self.type,
        }

    @classmethod
    def to_class(cls, data):
        return cls(
            public_key_hash=data['public_key_hash'],
            ticket=data.get("ticket"),
        )
