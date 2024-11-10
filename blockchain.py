import hashlib
import time
import json
import requests
import logging


class Block:
    def __init__(self, index, previous_hash, timestamp, data, hash, nonce=0):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.hash = hash
        self.nonce = nonce


class Blockchain:
    def __init__(self, difficulty=4):
        self.chain = []
        self.longest_chain = []  # To store the longest valid chain
        self.nodes = set(["node1:5000", "node2:5000", "node3:5000"])
        self.difficulty = difficulty
        self.create_genesis_block()
        # A set to store other node URLs
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("blockchain_app.log")
            ]
        )

    def create_genesis_block(self):
        # Create the first block (genesis block)
        genesis_block = Block(0, "0", int(time.time()), "Genesis Block", self.hash_block(
            0, "0", int(time.time()), "Genesis Block", 0), 0)
        self.chain.append(genesis_block)
        self.longest_chain = self.chain
        logging.info(f"genesis longest chain: {self.longest_chain}")

    def get_longest_chain(self):
        """
        Returns the longest chain. If this node's chain is corrupted, it will try to fetch
        the longest chain from other nodes.
        """
        return [vars(block) for block in self.longest_chain]

    def compare_and_replace_chain(self, new_chain):
        """
        Compares the current chain with the new chain from another node.
        If the new chain is longer and valid, replace the current chain with it.
        """
        logging.info(new_chain)
        if len(new_chain) > len(self.chain):
            self.chain = [Block(**block) if isinstance(block, dict)
                          else block for block in new_chain]
            self.longest_chain = new_chain  # Update the longest chain
            logging.warning(
                "Replaced local chain with a longer chain from another node.")
            return True
        return False

    def hash_block(self, index, previous_hash, timestamp, data, nonce):
        block_string = f"{index}{previous_hash}{data}{nonce}"
        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()

    def proof_of_work(self, index, previous_hash, timestamp, data):
        nonce = 0
        while True:
            hash_attempt = self.hash_block(
                index, previous_hash, timestamp, data, nonce)
            if hash_attempt[:self.difficulty] == "0" * self.difficulty:
                return hash_attempt, nonce
            nonce += 1

    def add_block(self, data):
        previous_block = self.chain[-1]
        timestamp = int(time.time())
        new_index = len(self.chain)

        # Find a valid hash and nonce using proof of work
        hash_result, nonce = self.proof_of_work(
            new_index, previous_block.hash, timestamp, data)

        new_block = Block(new_index, previous_block.hash,
                          timestamp, data, hash_result, nonce)
        try:
            self.broadcast_new_block(new_block)
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
            if current_block.hash != self.hash_block(current_block.index, current_block.previous_hash,
                                                     current_block.timestamp, current_block.data, current_block.nonce):
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

    def validate_block(self, block):
        # Block validation rules
        previous_block = self.chain[-1]
        if block.previous_hash != previous_block.hash:
            return False
        # Check that the block hash is correct and meets difficulty requirements
        if block.hash != self.hash_block(block.index, block.previous_hash, block.timestamp, block.data, block.nonce):
            return False
        if block.hash[:self.difficulty] != "0" * self.difficulty:
            return False
        if not self.validate_chain():
            return False
        self.chain.append(block)
        self.longest_chain = self.chain
        logging.info(f"genesis longest chain: {self.longest_chain}")
        return True

    def broadcast_new_block(self, new_block):
        # Simulate broadcasting to other nodes
        logging.info(f"genesis longest chain: {self.longest_chain}")
        for node in self.nodes:
            try:
                logging.info(f"Attempting to broadcast to node: {node}")

                # Simulate sending the new block
                response = requests.post(
                    f'http://{node}/validate_block', json={'block': vars(new_block)})

                if response.status_code == 200:
                    logging.info(f"Successfully broadcasted to node {node}")
                else:
                    logging.error(
                        f"Error broadcasting to {node}, Status Code: {response.status_code}")

            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to contact node {node}. Error: {e}")

    def get_chain(self):
        return [vars(block) for block in self.chain]

    def __repr__(self):
        return json.dumps([vars(block) for block in self.chain], indent=4)

    def add_node(self, node_url):
        self.nodes.add(node_url)