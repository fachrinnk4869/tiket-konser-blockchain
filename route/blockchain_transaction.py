import logging
from flask import Blueprint, jsonify, request, session
from blockchain import Block, Blockchain, Transaction
import requests
from transaction.transaction_input import TransactionInput
from transaction.transaction_output import TransactionOutput
from wallet import Owner
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


@blockchain_bp.route('/get_user', methods=['GET'])
def get_user():
    owner = session.get('owner')
    return jsonify({"owner": owner}), 200


@blockchain_bp.route('/add_ticket', methods=['POST'])
def add_ticket():
    data = request.get_json()
    ticket_details = data.get('ticket_details')
    event = ticket_details.get('event')
    seat = ticket_details.get('seat')
    owner_id = ticket_details.get('owner')
    logging.warning(f"halo {ticket_details}")
    if not ticket_details:
        return jsonify({"message": "Missing required data: ticket_details or node"}), 400

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        # Insert the new ticket into the database
        cursor.execute('INSERT INTO tickets (event, seat, status) VALUES (?, ?, ?)',
                       (event, seat, 'jual'))
        conn.commit()
        ticket_id = cursor.lastrowid

        # Create the transaction inputs and outputs
        inputs = []
        outputs = [{
            "amount": 50,  # Example amount
            "ticket": ticket_id,
            "public_key_hash": Owner.get_public_key(owner_id)
        }]
        # to class
        outputs = [TransactionOutput.to_class(output) for output in outputs]

        # Create the transaction
        logging.warning(f"halo {session}")
        transaction = Transaction(
            owner=Owner.get_public_key(owner_id), inputs=inputs, outputs=outputs, owner_id=owner_id)
        transaction.tx_id = transaction.generate_tx_id()
        transaction.sign()

        # Add the transaction to the blockchain
        blockchain.add_transaction_to_block(transaction)

        # Mine a new block
        new_block = blockchain.add_block()
        if new_block:
            blockchain.save_to_file()
            return jsonify({"message": "Ticket added and block mined", "block": new_block.to_dict()}), 201
        else:
            # If mining fails, delete the ticket from the database
            cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
            conn.commit()
            return jsonify({"message": "Mining failed, ticket removed"}), 400


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
    ticket_id = data.get("ticket_id")
    buyer_id = session.get('owner')

    if not ticket_id or not buyer_id:
        return jsonify({"message": "Missing required data: ticket_id or buyer_id"}), 400

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        # Check if the ticket exists and is available for sale
        cursor.execute("SELECT status FROM tickets WHERE id = ?", (ticket_id,))
        ticket = cursor.fetchone()
        if not ticket or ticket[0] != 'jual':
            return jsonify({"message": "Ticket not available for sale"}), 400

        # Update the ticket status to 'sold' and assign it to the buyer
        cursor.execute("UPDATE tickets SET status = ?, owner_id = ? WHERE id = ?",
                       ('sold', buyer_id, ticket_id))
        conn.commit()

        # Create the transaction outputs
        outputs = [{
            "amount": 50,  # Example amount
            "ticket": ticket_id,
            "public_key_hash": Owner.get_public_key(buyer_id)
        }]
        outputs = [TransactionOutput.to_class(output) for output in outputs]

        # Create the transaction without signature
        transaction = Transaction(
            owner=Owner.get_public_key(buyer_id), inputs=[], outputs=outputs, owner_id=buyer_id)
        transaction.tx_id = transaction.generate_tx_id()

        # Add the transaction to the blockchain
        blockchain.add_transaction_to_block(transaction)

        # Mine a new block
        new_block = blockchain.add_block()
        if new_block:
            blockchain.save_to_file()
            return jsonify({"message": "Ticket purchased and block mined", "block": new_block.to_dict()}), 201
        else:
            # If mining fails, revert the ticket status
            cursor.execute(
                "UPDATE tickets SET status = ? WHERE id = ?", ('jual', ticket_id))
            conn.commit()
            return jsonify({"message": "Mining failed, ticket status reverted"}), 400


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
