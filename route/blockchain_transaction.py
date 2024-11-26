from flask import Blueprint, jsonify, request
from blockchain import Block, Blockchain, Transaction
import requests
from transaction.transaction_input import TransactionInput
from transaction.transaction_output import TransactionOutput
import sqlite3
import uuid

# SQLite database path
DATABASE = 'tickets.db'

# Initialize Flask Blueprint
blockchain_bp = Blueprint('blockchain', __name__)
blockchain = Blockchain(difficulty=4)  # Set difficulty level for proof of work


@blockchain_bp.route('/validate_block', methods=['POST'])
def validate_block():
    block_data = request.json.get('block')
    utxo_pool = request.json.get('utxo_pool')
    block = Block(**block_data)
    # logging.WARNING(f"halo {block}")

    if blockchain.validate_block(block, utxo_pool):
        return jsonify({"message": "Block is valid"}), 200
    return jsonify({"message": "Invalid block"}), 400


@blockchain_bp.route('/mine_block', methods=['POST'])
def mine_block():
    new_block = blockchain.add_block()
    if new_block:
        blockchain.save_to_file()
        return jsonify({"message": "Block mined", "block": new_block.to_dict()}), 201
    return jsonify({"message": "Mining failed"}), 400


@blockchain_bp.route("/buy_ticket", methods=["POST"])
def buy_ticket():
    data = request.get_json()

    # Extract transaction details from the request body
    ticket_id = data.get("ticket")
    buyer_node = data.get("node")

    if not ticket_id or not buyer_node:
        return jsonify({"message": "Missing required data: ticket or node"}), 400

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        # Check current status of the ticket
        cursor.execute("SELECT status FROM tickets WHERE id = ?", (ticket_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"message": "Ticket not found"}), 404

        current_status = result[0]

        # If the ticket is already purchased
        if current_status == "beli":
            return jsonify({"message": "Ticket already purchased"}), 400
        # Generate a random token
        token_valid = str(uuid.uuid4())

        # Store the token for validation in create_transaction
        cursor.execute(
            "INSERT INTO tokens (token, ticket_id) VALUES (?, ?)", (token_valid, ticket_id))
        conn.commit()
        # Proceed with the transaction
        transaction_data = {
            "outputs": [{
                "node": buyer_node,
                "amount": 50,  # Example amount
                "ticket": ticket_id
            }],
            "token_valid": token_valid
        }

        # Hit /create_transaction endpoint
        response = requests.post(
            f"http://{buyer_node}:5000/create_transaction", json=transaction_data)

        if response.status_code == 201:
            # Update the ticket status to 'beli'
            cursor.execute(
                "UPDATE tickets SET status = 'beli' WHERE id = ?", (ticket_id,))
            conn.commit()
            return jsonify({"message": "Ticket purchased successfully"}), 200
        else:
            return jsonify({"message": "Transaction failed"}), 400


@blockchain_bp.route("/create_transaction", methods=["POST"])
def create_transaction():
    data = request.get_json()

    # Extract transaction details from the request body
    outputs_data = data.get("outputs", [])
    token_valid = data.get("token_valid", 1)

    # Validate token
    if not token_valid:
        return jsonify({"status": "error", "message": "Missing token"}), 400

    # Ensure this key is provided in the request
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        response = requests.get(
            f'http://localhost:5000/get_seatEvent')
        if response.status_code == 200:  # Ensure the request was successful
            data = response.json()
        # Check if the token is valid
        cursor.execute(
            "SELECT ticket_id FROM tokens WHERE token = ?", (token_valid,))
        token_data = cursor.fetchone()
        if not token_data and not data['event']:
            return jsonify({"status": "error", "message": "Invalid token or not have event, seat available"}), 400
        elif token_data:
            # Delete the token after validation (one-time use)
            cursor.execute(
                "DELETE FROM tokens WHERE token = ?", (token_valid,))
            conn.commit()

    # Create the inputs
    inputs = []
    for output_data in outputs_data:
        try:
            # Get the previous transaction hash for the input owner
            previous_index, previous_transaction_hash = blockchain.get_last_transaction_ticket(
                owner.public_key_hex, output_data.get("ticket"))

            if not previous_index or not previous_transaction_hash:
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

    return jsonify({"status": "success", "message": "Transaction created"}), 201


@blockchain_bp.route('/get_longest_chain', methods=['GET'])
def get_longest_chain():
    # Return the longest valid chain this node knows about
    return jsonify({"chain": blockchain.get_longest_chain()}), 200
