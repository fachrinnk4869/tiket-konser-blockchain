import hashlib
import time
import json
import requests
import logging
import os
import json
import binascii
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
from transaction.transaction_input import TransactionInput
from transaction.transaction_output_balance import TransactionOutputBalance
from transaction.transaction_output_ticket import TransactionOutputTicket
from wallet import Owner, Transaction
from interface import BlockchainInterface, ClassInterface


import json


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        """Override default to handle custom objects."""
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        return super().default(obj)
 # For other objects, use the default serialization


class Block(ClassInterface):
    def __init__(self, index, previous_hash, timestamp, transactions, hash, nonce=0):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.transactions = transactions  # List of Transaction objects
        self.hash = hash
        self.nonce = nonce

    def to_dict(self):
        # Convert transactions to dict format
        block_data = {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "transactions": [t.to_dict() for t in self.transactions],
            "hash": self.hash,
            "nonce": self.nonce
        }
        return block_data

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def to_class(cls, data):
        transactions = [Transaction.to_class(t) for t in data["transactions"]]
        return cls(
            index=data["index"],
            previous_hash=data["previous_hash"],
            timestamp=data["timestamp"],
            hash=data["hash"],
            nonce=data["nonce"],
            transactions=transactions
        )


class Blockchain(BlockchainInterface):
    def __init__(self, difficulty=2):
        self.chain = []
        self.current_transactions = []  # Transactions waiting to be added
        self.longest_chain = []  # To store the longest valid chain
        self.difficulty = difficulty
        self.utxo_pool = {}
        self.nodes = set(["localhost:5000"])

        # A set to store other node URLs
        self.setup_logging()
        # Path untuk menyimpan file blockchain
        self.file_path = 'blockchain.json'
        self.load_from_file()

    def save_to_file(self):
        """Save the blockchain to a file."""
        with open(self.file_path, 'w') as file:
            data = {
                "chain": [block.to_dict() for block in self.chain],
                "difficulty": self.difficulty,
                "utxo_pool": self.utxo_pool
            }
            json.dump(data, file, cls=CustomJSONEncoder)
        print("Blockchain saved to file.")

    def load_from_file(self):
        """Load the blockchain from a file."""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as file:
                data = json.load(file)
                self.chain = [Block.to_class(block_data)
                              for block_data in data["chain"]]

                self.difficulty = data["difficulty"]

                self.utxo_pool = self.deserialize_utxo_pool(data["utxo_pool"])

            print("Blockchain loaded from file.")

        else:
            self.create_genesis_block()
            print("No blockchain file found. Starting with a new blockchain.")

    def setup_logging(self):
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("blockchain_app.log")
            ]
        )

    def add_transaction_to_pool(self, transaction: Transaction):
        """
        Add a transaction to the blockchain and update the UTXO pool.
        :param transaction: The transaction to add to the blockchain.
        """
        # Add the outputs to the UTXO pool
        for i, output in enumerate(transaction.outputs):
            self.utxo_pool[f"{transaction.tx_id}:{i}"] = output

        # Remove the spent UTXOs from the UTXO pool
        for input_tx in transaction.inputs:
            utxo_key = f"{input_tx.transaction_hash}:{input_tx.output_index}"
            if utxo_key in self.utxo_pool:
                del self.utxo_pool[utxo_key]

        # Add the transaction to the blockchain
        self.current_transactions.append(transaction)

    def get_balance(self, owner) -> int:
        """
        Calculate the balance for a given public key hash by summing all unspent outputs.
        :param public_key_hash: The public key hash to check balance for.
        :return: The total balance.
        """
        return sum(int(output.amount) for output in self.utxo_pool.values() if output.public_key_hash == owner and isinstance(output, TransactionOutputBalance))

    def get_tickets(self, owner) -> int:
        """
        Calculate the balance for a given public key hash by summing all unspent outputs.
        :param public_key_hash: The public key hash to check balance for.
        :return: The total balance.
        """
        return [int(output.ticket) for output in self.utxo_pool.values() if output.public_key_hash == owner and isinstance(output, TransactionOutputTicket)]

    def get_last_transaction_ticket(self, ticket):
        """
        Retrieve the last transaction for a specific owner.
        This assumes that transactions are stored in the blockchain blocks.
        """
        # Traverse the blockchain in reverse to find the most recent transaction
        for block in reversed(self.chain):
            for transaction in block.transactions:
                # Check if the owner matches in the outputs
                for i, output in enumerate(transaction.outputs):
                    logging.warning(f"ticket = {ticket}")
                    if isinstance(output, TransactionOutputTicket) and int(output.ticket) == int(ticket):
                        return output.public_key_hash, i, transaction.tx_id
        return None, None, None  # Return None if no transaction is found

    def get_utxo_pool(self):
        """
        Return the current UTXO pool.
        :return: Dictionary of UTXOs.
        """
        # Convert each UTXO to a dictionary and return as a JSON string
        serialized_utxo_pool = {
            tx_id: output.to_dict() for tx_id, output in self.utxo_pool.items()
        }
        return serialized_utxo_pool

    def create_transaction(self, **kwargs):
        transaction = Transaction(**kwargs)
        self.current_transactions.append(transaction)
        return transaction

    def create_genesis_block(self):
        # Create the first block (genesis block)
        genesis_block = Block(0, "0", int(time.time()), [], self.hash_block(
            0, "0", 0), 0)
        self.chain.append(genesis_block)
        self.longest_chain = self.chain
        logging.info(f"genesis longest chain: {self.longest_chain}")

    def get_longest_chain(self):
        """
        Returns the longest chain. If this node's chain is corrupted, it will try to fetch
        the longest chain from other nodes.
        """
        return [block.to_dict() for block in self.longest_chain]

    def hash_block(self, index, previous_hash, nonce):
        block_string = f"{index}{previous_hash}{nonce}"
        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()

    def proof_of_work(self, index, previous_hash):
        nonce = 0
        while True:
            hash_attempt = self.hash_block(
                index, previous_hash, nonce)
            if hash_attempt[:self.difficulty] == "0" * self.difficulty:
                return hash_attempt, nonce
            nonce += 1

    def add_block(self):
        previous_block = self.chain[-1]
        timestamp = int(time.time())
        new_index = len(self.chain)

        # Find a valid hash and nonce using proof of work
        hash_result, nonce = self.proof_of_work(
            new_index, previous_block.hash)

        new_block = Block(new_index, previous_block.hash,
                          timestamp, self.current_transactions, hash_result, nonce)
        # Reset the list of current transactions
        self.current_transactions = []
        try:
            if self.broadcast_new_block(new_block, self.utxo_pool):
                return new_block
        except requests.exceptions.RequestException as e:
            return None

    def validate_chain(self):
        # Start from the second block, since the first (genesis) block doesn't have a previous block
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Validate that the previous block's hash is correct
            if current_block.previous_hash != previous_block.hash:
                logging.error(
                    f"Blockchain invalid! Block {current_block.index} has an incorrect previous_hash.")
                return False

            # Validate that the current block's hash is correct
            if current_block.hash != self.hash_block(current_block.index, current_block.previous_hash, current_block.nonce):
                logging.error(
                    f"Blockchain invalid! Block {current_block.index} has an incorrect hash.")
                return False

            # Validate proof of work (difficulty requirement)
            if current_block.hash[:self.difficulty] != "0" * self.difficulty:
                logging.error(
                    f"Blockchain invalid! Block {current_block.index} does not meet difficulty.")
                return False

        # If all blocks are valid
        logging.info("Blockchain is valid.")
        return True
    # Function to deserialize utxo_pool back to the original format

    def deserialize_utxo_pool(self, utxo_pool_data):
        # logging.WARNING(utxo_pool_data.amount)
        # Check if the data is a string and try to deserialize it
        if isinstance(utxo_pool_data, str):
            # Deserialize string to dictionary
            utxo_pool_data = json.loads(utxo_pool_data)

        # Ensure the data is now a dictionary
        if isinstance(utxo_pool_data, dict):
            deserialized_utxo_pool = {}

            for key, value in utxo_pool_data.items():
                # Check if value is a dictionary that can be converted into a TransactionOutputTicket
                if isinstance(value, dict) and 'public_key_hash' in value and 'ticket' in value:
                    deserialized_utxo_pool[key] = TransactionOutputTicket.to_class(
                        value)
                elif isinstance(value, dict) and 'public_key_hash' in value and 'amount' in value:
                    deserialized_utxo_pool[key] = TransactionOutputBalance.to_class(
                        value)
                else:
                    # Keep as-is if it's not a TransactionOutputTicket
                    deserialized_utxo_pool[key] = value

            return deserialized_utxo_pool
        else:
            raise ValueError(
                "Expected a dictionary, but received something else.")

    def validate_block(self, block, utxo_pool):
        # Block validation rules
        previous_block = self.chain[-1]
        if block.previous_hash != previous_block.hash:
            return False
        print("Previous hash validated")
        # Check that the block hash is correct and meets difficulty requirements
        result = requests.post(
            f'http://localhost:5000/blockchain/validate_sign', json={'ticket_id': block.to_dict()['transactions'][0]['outputs'][0]['ticket']})
        if result.status_code != 200 and result.status_code != 201:
            logging.error(
                f"Failed to validate signature for block {block.index}. Status Code: {result.status_code}")
            return False
        print("Signature validated")
        if block.hash != self.hash_block(block.index, block.previous_hash, block.nonce):
            return False
        print("Hash validated")
        if block.hash[:self.difficulty] != "0" * self.difficulty:
            return False
        print("Difficulty validated")
        if not self.validate_chain():
            return False
        print("Chain validated")
        # logging.warning(f"UTXO poool = {utxo_pool}")
        self.utxo_pool = self.deserialize_utxo_pool(utxo_pool)
        self.chain.append(block)
        self.longest_chain = self.chain
        logging.info(f"genesis longest chain: {self.longest_chain}")
        return True

    def broadcast_new_block(self, new_block, utxo_pool):
        # Simulate broadcasting to other nodes
        logging.info(f"genesis longest chain: {self.longest_chain}")
        for node in self.nodes:
            try:
                logging.info(f"Attempting to broadcast to node: {node}")

                # Simulate sending the new block
                response = requests.post(
                    f'http://{node}/blockchain/validate_block', json={'block': new_block.to_dict(), 'utxo_pool': json.dumps(utxo_pool, cls=CustomJSONEncoder)})

                if response.status_code == 200:
                    logging.info(f"Successfully broadcasted to node {node}")
                else:
                    logging.error(
                        f"Error broadcasting to {node}, Status Code: {response.status_code}")
                    return False
            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to contact node {node}. Error: {e}")
                return False
        return True

    def get_chain(self):
        return [block.to_dict() for block in self.chain]

    def __repr__(self):
        return json.dumps([block.to_dict() for block in self.chain], indent=4)

    def add_node(self, node_url):
        self.nodes.add(node_url)
