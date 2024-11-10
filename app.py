from flask import Flask, jsonify, request
import logging
from blockchain import Block, Blockchain
import requests
app = Flask(__name__)
blockchain = Blockchain(difficulty=4)  # Set difficulty level for proof of work


@app.route('/', methods=['GET'])
def get_blockchain():
    return jsonify(blockchain.get_chain())


@app.route('/add_block', methods=['POST'])
def add_block():
    data = request.json.get('data')
    new_block = blockchain.add_block(data)
    if new_block:
        return jsonify({"message": "Block added", "block": vars(new_block)}), 201
    return jsonify({"message": "Failed to add block"}), 400


@app.route('/validate_block', methods=['POST'])
def validate_block():
    block_data = request.json.get('block')
    block = Block(**block_data)

    if blockchain.validate_block(block):
        return jsonify({"message": "Block is valid"}), 200
    return jsonify({"message": "Invalid block"}), 400


@app.route('/mine_block', methods=['POST'])
def mine_block():
    data = request.json.get('data')
    new_block = blockchain.add_block(data)
    if new_block:
        return jsonify({"message": "Block mined", "block": vars(new_block)}), 201
    return jsonify({"message": "Mining failed"}), 400


@app.route('/crash_block', methods=['POST'])
def crash_block():
    # Get the block index and new data from the request
    block_data = request.json.get('block')
    block_index = block_data.get('index')
    new_data = block_data.get('data')

    # Validate index
    logging.info(
        f"index of block: {block_index}")
    if int(block_index) >= len(blockchain.chain):
        return jsonify({"message": "Invalid block index"}), 400

    # Get the block to crash
    block_to_crash = blockchain.chain[block_index]

    # Modify the block's data (this simulates the crash)
    block_to_crash.data = new_data
    block_to_crash.hash = blockchain.hash_block(
        block_to_crash.index, block_to_crash.previous_hash, block_to_crash.timestamp, block_to_crash.data, block_to_crash.nonce)

    # Log the crash
    logging.info(
        f"Block at index {block_index} crashed with new data: {new_data}")

    # Simulate broadcast of the crashed block to other nodes (optional)
    blockchain.broadcast_new_block(block_to_crash)

    return jsonify({
        "message": f"Block at index {block_index} has been crashed.",
        "block": vars(block_to_crash)
    }), 200


@app.route('/fix_blockchain', methods=['POST'])
def fix_blockchain():
    # If the blockchain is corrupted, compare with the longest known valid chain
    if not blockchain.validate_chain():
        logging.warning("Blockchain is corrupted. Attempting to fix...")

        # Try to fetch the longest chain from other nodes
        real_longest_chain = []
        for node in blockchain.nodes:
            try:
                logging.warning(f"Requesting longest chain from node {node}")
                response = requests.get(f'http://{node}/get_longest_chain')
                if response.status_code == 200:
                    longest_chain = response.json().get('chain')
                    logging.warning(f"longest chain: {longest_chain}")
                    if len(longest_chain) > len(real_longest_chain):
                        real_longest_chain = longest_chain
                        continue
                else:
                    logging.error(
                        f"Failed to get the chain from {node}, Status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to contact node {node}. Error: {e}")
        if real_longest_chain:
            blockchain.compare_and_replace_chain(real_longest_chain)
            return jsonify({"message": "Blockchain fixed by replacing with the longest chain."}), 200
        return jsonify({"message": "Could not fix blockchain with any valid chain."}), 400
    return jsonify({"message": "Blockchain is already valid."}), 200


@app.route('/get_longest_chain', methods=['GET'])
def get_longest_chain():
    # Return the longest valid chain this node knows about
    return jsonify({"chain": blockchain.get_longest_chain()}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
