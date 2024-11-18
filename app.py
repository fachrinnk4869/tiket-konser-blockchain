import os
from flask import Flask, jsonify, request
import logging
from blockchain import Block, Blockchain, Transaction
import requests
from flask import Flask, request, jsonify
from Crypto.PublicKey import RSA
from wallet import Owner, Transaction
from transaction.transaction_input import TransactionInput
from transaction.transaction_output import TransactionOutput
import sqlite3

# SQLite database path
DATABASE = 'tickets.db'

# Initialize database if not exists


def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS tickets (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            event TEXT,
                            seat TEXT
                        )''')  # Status: "jual" or "beli"
        conn.commit()


# Call init_db on app startup
init_db()

app = Flask(__name__)
blockchain = Blockchain(difficulty=4)  # Set difficulty level for proof of work
# Load blockchain data on startup
blockchain.load_from_file()
# Generate RSA keys for the owner (Alice) on app startup
rsa_key_dir = '/rsa_keys/'  # Path inside the container's volume

if not os.path.exists(rsa_key_dir):
    os.makedirs(rsa_key_dir)

private_key_path = os.path.join(rsa_key_dir, 'private_key.pem')
public_key_path = os.path.join(rsa_key_dir, 'public_key.pem')
# Check if keys already exist
if not os.path.exists(private_key_path) or not os.path.exists(public_key_path):
    # Generate RSA keys
    private_key = RSA.generate(2048)
    public_key = private_key.publickey()

    # Save private key
    with open(private_key_path, 'wb') as private_file:
        private_file.write(private_key.export_key())

    # Save public key
    with open(public_key_path, 'wb') as public_file:
        public_file.write(public_key.export_key())

    print("Keys generated and saved.")
else:
    print("Keys already exist, loading from files.")

# Load the saved keys on app startup
with open(private_key_path, 'rb') as private_file:
    private_key = RSA.import_key(private_file.read())

with open(public_key_path, 'rb') as public_file:
    public_key = RSA.import_key(public_file.read())

# Example: Alice object
owner = Owner(public_key_hex=public_key.export_key().decode(
    'utf-8'), private_key=private_key)
print(f"Public key: {owner.public_key_hex}")


@app.route('/', methods=['GET'])
def get_blockchain():
    return jsonify(blockchain.get_chain())


@app.route('/add_block', methods=['POST'])
def add_block():
    new_block = blockchain.add_block()
    if new_block:
        return jsonify({"message": "Block added", "block": new_block.to_dict()}), 201
    return jsonify({"message": "Failed to add block"}), 400


@app.route('/validate_block', methods=['POST'])
def validate_block():
    block_data = request.json.get('block')
    utxo_pool = request.json.get('utxo_pool')
    block = Block(**block_data)
    # logging.WARNING(f"halo {block}")

    if blockchain.validate_block(block, utxo_pool):
        return jsonify({"message": "Block is valid"}), 200
    return jsonify({"message": "Invalid block"}), 400


@app.route('/mine_block', methods=['POST'])
def mine_block():
    new_block = blockchain.add_block()
    if new_block:
        blockchain.save_to_file()
        return jsonify({"message": "Block mined", "block": new_block.to_dict()}), 201
    return jsonify({"message": "Mining failed"}), 400


@app.route('/crash_block', methods=['POST'])
def crash_block():
    # Get the block index and new data from the request
    logging.warning(f"Masuk sini")
    block_data = request.json.get('block')
    block_index = block_data.get('index')
    new_transactions = block_data.get('transactions')

    # Validate index
    logging.warning(f"Index of block to crash: {block_index}")

    # Check if the block index is valid
    if int(block_index) >= len(blockchain.chain):
        return jsonify({"message": "Invalid block index"}), 400

    # Get the block to crash
    block_to_crash = blockchain.chain[block_index]

    # Convert new transaction data into Transaction objects
    new_transactions_objects = [
        Transaction(**t) for t in new_transactions]

    # Modify the block's transactions (this simulates the crash)
    block_to_crash.transactions = new_transactions_objects

    # Recalculate the hash with the new data
    block_to_crash.hash = blockchain.hash_block(
        block_to_crash.index,
        block_to_crash.previous_hash,
        block_to_crash.timestamp,
        block_to_crash.transactions,
        block_to_crash.nonce
    )

    # Log the crash
    logging.warning(
        f"Block at index {block_index} crashed with new data: {new_transactions}")

    # Simulate broadcasting of the crashed block to other nodes (optional)
    blockchain.broadcast_new_block(block_to_crash)

    # Return response with updated block information
    return jsonify({
        "message": f"Block at index {block_index} has been crashed.",
        "block": block_to_crash.to_dict()  # Make sure to return the block as a dictionary
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


@app.route('/add_ticket', methods=['POST'])
def sell_ticket():
    data = request.json
    event = data.get('event')
    seat = data.get('seat')

    if not all([owner, event, seat]):
        return jsonify({"message": "Missing required fields"}), 400

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tickets (event, seat) VALUES (?, ?)",
                       (event, seat))
        conn.commit()

    return jsonify({"message": "Ticket listed for sale"}), 201


@app.route("/create_transaction", methods=["POST"])
def create_transaction():
    data = request.get_json()

    # Extract transaction details from the request body
    outputs_data = data.get("outputs", [])

    # Create the inputs
    inputs = []
    try:
        # Get the previous transaction hash for the input owner
        # Ensure this key is provided in the request
        previous_index, previous_transaction_hash = blockchain.get_last_transaction_for_owner(
            owner.public_key_hex)

        if not previous_transaction_hash:
            transaction_input = TransactionInput(
                transaction_hash="genesis",
                output_index="genesis"
            )
        else:
            transaction_input = TransactionInput(
                transaction_hash=previous_transaction_hash,
                output_index=previous_index
            )
        inputs.append(transaction_input)
    except KeyError:
        return jsonify({"status": "error", "message": "Invalid input format"}), 400

    outputs = []
    for output_data in outputs_data:
        node = output_data["node"]
        response = requests.get(
            f'http://{node}:5000/get_public_key')
        if response.status_code == 200:  # Ensure the request was successful
            try:
                data = response.json()  # Parse the JSON content
                # Extract the desired key
                transaction_output = TransactionOutput(
                    public_key_hash=data['public_key_hex'],
                    amount=output_data["amount"],
                    ticket=output_data.get("ticket"),
                )
            except ValueError:
                print("Response is not valid JSON.")
            except KeyError:
                print("Key 'public_key_hash' not found in the response.")
        else:
            print(
                f"Request failed with status code {response.status_code}")
        outputs.append(transaction_output)

    # Create the transaction
    transaction = Transaction(owner=owner, inputs=inputs, outputs=outputs)
    transaction.tx_id = transaction.generate_tx_id()
    # Sign the transaction
    transaction.sign()

    # Add the transaction to the blockchain
    blockchain.add_transaction_to_block(transaction)

    return jsonify({"status": "success", "message": "Transaction created and added to the blockchain"}), 201


@app.route('/get_longest_chain', methods=['GET'])
def get_longest_chain():
    # Return the longest valid chain this node knows about
    return jsonify({"chain": blockchain.get_longest_chain()}), 200


@app.route('/get_public_key', methods=['GET'])
def get_public_key_hash():
    # Call the method to get the public key hash
    public_key_hash = owner.to_dict()

    # Return it as a JSON response
    return jsonify(public_key_hash), 200


@app.route("/get_utxo_pool", methods=["GET"])
def get_utxo_pool():
    utxo_pool = blockchain.get_utxo_pool()
    return jsonify(utxo_pool), 200


@app.route("/get_balance", methods=["GET"])
def get_balance():
    balance = blockchain.get_balance(owner)
    return jsonify({"balance": balance}), 200


@app.route("/get_seatEvent", methods=["GET"])
def get_seatEvent():
    """
    Calculate the balance for a given public key hash by summing all unspent outputs.
    :param public_key_hash: The public key hash to check balance for.
    :return: The total balance.
    """
    # Lists to store the associated seats and events

    # Iterate over the UTXO pool and filter based on the owner's public key hash
    seats, events = [], []
    for output in blockchain.utxo_pool.values():
        if output.public_key_hash == owner.public_key_hex:
            # Add the seat and event associated with this UTXO output
            # Assuming `seat` is an attribute in TransactionOutput
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                try:
                    # Query untuk mencari UTXO yang cocok berdasarkan public_key_hash
                    query = """
                    SELECT seat, event
                    FROM tickets
                    WHERE id = ?
                    """
                    cursor.execute(query, (output.ticket,))
                    result = cursor.fetchone()

                    if result:
                        seat, event = result  # Assign hasil query ke variabel seat dan event
                        seats.append(seat)
                        events.append(event)

                except sqlite3.Error as e:
                    print(f"Database error: {e}")

    return jsonify({"seat": seats, "event": events}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
