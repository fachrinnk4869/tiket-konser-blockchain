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
from transaction.transaction_output import TransactionOutput
from wallet import Owner, Transaction


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # Check if the object is an instance of your custom class
        if isinstance(obj, TransactionOutput):
            return obj.to_dict()  # Use the to_dict method to convert it to a JSON-compatible format
        return super().default(obj)  # For other objects, use the default serialization


class Block:
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


class Blockchain:
    def __init__(self, difficulty=2):
        self.chain = []
        self.current_transactions = []  # Transactions waiting to be added
        self.longest_chain = []  # To store the longest valid chain
        self.nodes = set(["node1:5000", "node2:5000", "node3:5000"])
        self.difficulty = difficulty
        self.utxo_pool = {}

        # A set to store other node URLs
        self.setup_logging()
        # Path untuk menyimpan file blockchain
        self.file_path = 'blockchain.json'

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

                self.chain = [Block(
                    index=block_data["index"],
                    previous_hash=block_data["previous_hash"],
                    timestamp=block_data["timestamp"],
                    hash=block_data["hash"],
                    nonce=block_data["nonce"],
                    transactions=[
                        Transaction(
                            owner=Owner(
                                public_key_hex=t["owner"]["public_key_hex"],
                                private_key=None  # Jika private_key tidak diperlukan
                            ),
                            inputs=[TransactionInput(**input_data)
                                    for input_data in t["inputs"]],
                            outputs=[TransactionOutput(
                                **output_data) for output_data in t["outputs"]],
                            tx_id=t["tx_id"]
                        )
                        for t in block_data["transactions"]
                    ]
                ) for block_data in data["chain"]]

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

    def add_transaction_to_block(self, transaction: Transaction):
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
        return sum(output.amount for output in self.utxo_pool.values() if output.public_key_hash == owner.public_key_hex)

    def get_seatEvent(self, owner):
        """
        Calculate the balance for a given public key hash by summing all unspent outputs.
        :param public_key_hash: The public key hash to check balance for.
        :return: The total balance.
        """
        # Lists to store the associated seats and events

        # Iterate over the UTXO pool and filter based on the owner's public key hash
        seat, event = None, None
        for output in self.utxo_pool.values():
            if output.public_key_hash == owner.public_key_hex:
                # Add the seat and event associated with this UTXO output
                # Assuming `seat` is an attribute in TransactionOutput
                seat = output.seat
                # Assuming `event` is an attribute in TransactionOutput
                event = output.event

        return seat, event

    def get_last_transaction_for_owner(self, owner):
        """
        Retrieve the last transaction for a specific owner.
        This assumes that transactions are stored in the blockchain blocks.
        """
        # Traverse the blockchain in reverse to find the most recent transaction
        for block in reversed(self.chain):
            for transaction in block.transactions:
                # Check if the owner matches in the outputs
                for i, output in enumerate(transaction.outputs):
                    if output.public_key_hash == owner:
                        return i, transaction.tx_id
        return None, None  # Return None if no transaction is found

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

    def compare_and_replace_chain(self, new_chain):
        """
        Compares the current chain with the new chain from another node.
        If the new chain is longer and valid, replace the current chain with it.
        """
        logging.info(new_chain)

        if len(new_chain) > len(self.chain):
            # Convert the new chain blocks to Block objects, with proper Transaction instantiation
            self.chain = [
                Block(
                    # Unpack block fields except 'transactions'
                    **{key: value for key, value in block.items() if key != 'transactions'},
                    transactions=[
                        Transaction(**t) if isinstance(t, dict) else t for t in block.get('transactions', [])
                    ]  # Ensure each transaction is a Transaction object
                ) if isinstance(block, dict) else block
                for block in new_chain
            ]

            self.longest_chain = new_chain  # Update the longest chain
            logging.warning(
                "Replaced local chain with a longer chain from another node.")
            return True
        return False

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
            self.broadcast_new_block(new_block, self.utxo_pool)
            return new_block  # Return the block itself for API response
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
                # Check if value is a dictionary that can be converted into a TransactionOutput
                if isinstance(value, dict) and 'public_key_hash' in value and 'amount' in value:
                    deserialized_utxo_pool[key] = TransactionOutput.from_dict(
                        value)
                else:
                    # Keep as-is if it's not a TransactionOutput
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
        # Check that the block hash is correct and meets difficulty requirements
        # for t in block.transactions:
        #     logging.warning(f" {t}")
        # block.transactions = [Transaction(**t) for t in block.transactions]
        block.transactions = [
            Transaction(
                # Pass private_key or None if not needed
                owner=Owner(public_key_hex=t["owner"]
                            ["public_key_hex"], private_key=None),
                inputs=[TransactionInput(**input_data)
                        for input_data in t["inputs"]],
                outputs=[TransactionOutput(**output_data)
                         for output_data in t["outputs"]],
                tx_id=t["tx_id"]
            )
            for t in block.transactions
        ]
        if block.hash != self.hash_block(block.index, block.previous_hash, block.nonce):
            return False
        if block.hash[:self.difficulty] != "0" * self.difficulty:
            return False
        if not self.validate_chain():
            return False
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
                    f'http://{node}/validate_block', json={'block': new_block.to_dict(), 'utxo_pool': json.dumps(utxo_pool, cls=CustomJSONEncoder)})

                if response.status_code == 200:
                    logging.info(f"Successfully broadcasted to node {node}")
                else:
                    logging.error(
                        f"Error broadcasting to {node}, Status Code: {response.status_code}")

            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to contact node {node}. Error: {e}")

    def get_chain(self):
        return [block.to_dict() for block in self.chain]

    def __repr__(self):
        return json.dumps([block.to_dict() for block in self.chain], indent=4)

    def add_node(self, node_url):
        self.nodes.add(node_url)
