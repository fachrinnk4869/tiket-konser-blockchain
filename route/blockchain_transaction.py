import logging
from flask import Blueprint, jsonify, request, session, send_file
from blockchain import Block, Blockchain, Transaction
import requests
from transaction.transaction_input import TransactionInput
from transaction.transaction_output_balance import TransactionOutputBalance
from transaction.transaction_output_ticket import TransactionOutputTicket
from wallet import Owner
import sqlite3
import uuid
import io
import qrcode

# SQLite database path
DATABASE = 'tickets.db'

# Initialize Flask Blueprint
blockchain_bp = Blueprint('blockchain', __name__)
blockchain = Blockchain(difficulty=4)  # Set difficulty level for proof of work


@blockchain_bp.route('/validate_block', methods=['POST'])
def validate_block():
    block_data = request.json.get('block')
    utxo_pool = request.json.get('utxo_pool')
    block = Block.to_class(block_data)
    # logging.WARNING(f"halo {block}")

    if blockchain.validate_block(block, utxo_pool):
        return jsonify({"message": "Block is valid"}), 200
    return jsonify({"message": "Invalid block"}), 400


@blockchain_bp.route('/get_user', methods=['GET'])
def get_user():
    owner = session.get('owner')
    return jsonify({"owner": owner}), 200


@ blockchain_bp.route('/add_tickets', methods=['POST'])
def add_tickets():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tickets")
        count = cursor.fetchone()[0]
        if count > 0:
            return jsonify({"message": "Tickets already exist"}), 400
    tickets = [
        ('Concert A', 'A1', 50),
        ('Concert A', 'A2', 50),
        ('Concert A', 'A3', 50),
        ('Concert A', 'A4', 50),
        ('Concert A', 'A5', 50),
        ('Concert B', 'B1', 50),
        ('Concert B', 'B2', 50),
        ('Concert B', 'B3', 50),
        ('Concert B', 'B4', 50),
        ('Concert B', 'B5', 50)
    ]
    for ticket in tickets:
        response = requests.post('http://localhost:5000/blockchain/add_ticket', json={
            "ticket_details": {
                "event": ticket[0],
                "seat": ticket[1],
                "price": ticket[2],
                'owner': session.get('owner')
            }
        })
        if response.status_code != 201:

            logging.error(f"Failed to add ticket: {response.json()}")

            return jsonify({"message": "Failed to add ticket"}), 400
    new_block = blockchain.add_block()
    if new_block:
        blockchain.save_to_file()
        return jsonify({"message": "Tickets added and Mining successfully"}), 200
    else:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tickets")
            conn.commit()
        return jsonify({"message": "Failed to mining"}), 200


# /smart_contract/issue_ticket
@blockchain_bp.route('/sell_ticket', methods=['POST'])
def sell_ticket():
    data = request.get_json()
    ticket_id = data.get('ticket_id')
    price = data.get('price')

    prev_owner, output_index, tx_id = blockchain.get_last_transaction_ticket(
        ticket_id)
    if not prev_owner:
        return jsonify({"message": "Ticket not found"}), 400

    # issue ticket in solidity api
    response = requests.post('http://localhost:5000/smart_contract/issue_ticket', json={
        "ticket_id": ticket_id,
        "price": price,
        "owner": session.get('owner')
    })

    #
    if response.status_code != 200:
        return jsonify({"message": "Failed to issue ticket"}), 400

    # Create the transaction
    transactionInput = TransactionInput(
        transaction_hash=tx_id, output_index=output_index)

    signature = transactionInput.sign_transaction_input(
        Owner.get_private_key(session.get('owner'), import_key=False))
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tickets SET sign = ?,price = ?, status = 'jual' WHERE id = ?",
                       (signature, price, ticket_id))
        conn.commit()

    return jsonify({"message": "Ticket listed for sale"}), 200


@blockchain_bp.route('/validate_sign', methods=['POST'])
def validate_sign():
    data = request.get_json()
    ticket_id = data.get('ticket_id')

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT sign FROM tickets WHERE id = ?", (ticket_id,))
        result = cursor.fetchone()
        signature = result[0]
        if signature:
            logging.warning(str(signature))
            prev_owner, output_index, tx_id = blockchain.get_last_transaction_ticket(
                ticket_id)
            logging.warning(f"prev owner: {prev_owner}")
            transaction_input = TransactionInput(
                transaction_hash=tx_id, output_index=output_index)  # Dummy values for initialization
            if transaction_input.validate_transaction_input(prev_owner, signature):
                return jsonify({"message": "Signature is valid"}), 200
            else:
                return jsonify({"message": "Invalid signature"}), 400

    return jsonify({"message": "Signature not yet initialized"}), 201


@blockchain_bp.route('/add_ticket', methods=['POST'])
def add_ticket():
    data = request.get_json()
    ticket_details = data.get('ticket_details')
    event = ticket_details.get('event')
    seat = ticket_details.get('seat')
    price = ticket_details.get('price')
    owner_id = ticket_details.get('owner')
    # logging.warning(f"halo {ticket_details}")
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE username = ?",
                       (session.get('owner'),))
        result = cursor.fetchone()
        role = result[0]
    if not role == 'admin':
        return jsonify({"message": "Unauthorized access"}), 403
    if not ticket_details:
        return jsonify({"message": "Missing required data: ticket_details or node"}), 400

    with sqlite3.connect(DATABASE) as conn:
        try:
            cursor = conn.cursor()

            # Insert the new ticket into the database
            cursor.execute('INSERT INTO tickets (event, seat, price, status) VALUES (?, ?, ?, ?)',
                           (event, seat, price, 'available'))
            conn.commit()
            ticket_id = cursor.lastrowid

            # Create the transaction inputs and outputs
            inputs = []
            outputs = [{
                "ticket": ticket_id,
                "public_key_hash": Owner.get_public_key(owner_id)
            }]
            # to class
            outputs = [TransactionOutputTicket.to_class(
                output) for output in outputs]

            # Create the transaction
            transaction = Transaction(
                owner=Owner.get_public_key(owner_id), inputs=inputs, outputs=outputs, owner_id=owner_id)
            transaction.tx_id = transaction.generate_tx_id()

        # Add the transaction to the blockchain
            blockchain.add_transaction_to_pool(transaction)

            return jsonify({"message": "Ticket added"}), 201
        except Exception as e:
            # If mining fails, delete the ticket from the database
            cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
            conn.commit()
            return jsonify({"message": "Add ticket failed, ticket removed"}), 400


@blockchain_bp.route('/mine_block', methods=['POST'])
def mine_block():
    if not blockchain.current_transactions:
        return jsonify({"message": "No transactions to mine"}), 400
    new_block = blockchain.add_block()
    if new_block:
        blockchain.save_to_file()
        return jsonify({"message": "Block mined", "block": new_block.to_dict()}), 201
    return jsonify({"message": "Mining failed"}), 400


@blockchain_bp.route('/market', methods=['GET'])
def market():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tickets WHERE status = 'jual'")
        tickets = cursor.fetchall()
        ticket_to_dict = [{
            "id": ticket[0],
            "event": ticket[1],
            "seat": ticket[2],
            "price": ticket[3],
            "status": ticket[4]
        } for ticket in tickets]
        return jsonify({"tickets": ticket_to_dict}), 200


# /smart_contract/create_transaction
@blockchain_bp.route('/buy_ticket', methods=['POST'])
def buy_ticket():
    data = request.get_json()
    ticket_id = data.get('ticket_id')

    prev_owner, _, _ = blockchain.get_last_transaction_ticket(
        ticket_id)
    logging.warning(f"prev owner: {prev_owner}")
    if not prev_owner:
        return jsonify({"message": "Ticket not found"}), 400
    # response = smart_contract.create_transaction(
    #     buyer, seller, ticket_id, price)
    response = requests.post('http://localhost:5000/smart_contract/create_transaction', json={
        "ticket_id": ticket_id,
        "owner": session.get('owner')
    })
    if response.status_code != 200:
        return jsonify({"message": "Failed to create transaction"}), 400
    return jsonify({"message": "Transaction Created", "response": response.json()}), 200


# /smart_contract/process_payment
@blockchain_bp.route('/process_payment', methods=['POST'])
def process_payment():
    buyer = Owner.get_public_key(session.get('owner'))
    data = request.get_json()
    tx_hash = data.get('tx_hash')
    owner = session.get('owner')
    # response = smart_contract.process_payment(buyer, amount, id)
    response = requests.post('http://localhost:5000/smart_contract/process_payment', json={
        "tx_hash": tx_hash,
        "owner": owner
    })
    if response:
        response = response.json()
        amount = response["price"]
        prev_owner, output_index, tx_id = blockchain.get_last_transaction_ticket(
            response["ticket_id"])
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                        UPDATE tickets SET status = 'available' WHERE id = ?
                    """, (response["ticket_id"],))  # transaction[0] is the id
            cursor.execute(
                "SELECT sign FROM tickets WHERE id = ?", (response["ticket_id"],))
            result = cursor.fetchone()
            signature = result[0]
        # Create the transaction inputs and outputs
        inputs = [{
            "tx_id": tx_id,
            "output_index": output_index,
            'public_key_hash': prev_owner,
            'signature': signature,
        }
        ]
        inputs = [TransactionInput.to_class(
            input) for input in inputs]
        outputsticket = [{
            "ticket": response["ticket_id"],
            "public_key_hash": buyer,
        }]
        outputsbalance = [{
            "amount": amount,
            "public_key_hash": prev_owner
        }]
        # to class
        outputsticket = [TransactionOutputTicket.to_class(
            output) for output in outputsticket]

        outputsbalance = [TransactionOutputBalance.to_class(
            output) for output in outputsbalance]
        outputs = outputsticket + outputsbalance

        # Create the transaction
        transaction = Transaction(
            owner=prev_owner, inputs=inputs, outputs=outputs)
        transaction.tx_id = transaction.generate_tx_id()

    # Add the transaction to the blockchain
        blockchain.add_transaction_to_pool(transaction)

        return jsonify({"message": "Payment and Ticket transferred", "response": response}), 200

    return jsonify({"message": "Payment failed", "response": response}), 400


@blockchain_bp.route('/get_qr/<int:ticket_id>', methods=['GET'])
def get_qr(ticket_id):
    owner = Owner.get_public_key(session.get('owner'))
    if not owner:
        return jsonify({"message": "Unauthorized access"}), 403
    # Data to encode in the QR code
    data = ""
    for block in reversed(blockchain.chain):
        for transaction in block.transactions:
            # Check if the owner matches in the outputs
            unspent_ticket = blockchain.utxo_pool.get(f"{transaction.tx_id}:0")
            if unspent_ticket is not None and unspent_ticket.public_key_hash == owner and unspent_ticket.ticket == ticket_id:
                # logging.warning(f"transaction.outputs = {output.ticket}")
                data = f"{transaction.tx_id}:0"

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)

    # Create an image from the QR code
    img = qr.make_image(fill_color="black", back_color="white")

    # Save the image to a BytesIO stream
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    # Serve the image as a response
    return send_file(img_io, mimetype='image/png')


@blockchain_bp.route('/get_my_tickets', methods=['GET'])
def get_my_ticket():
    owner = Owner.get_public_key(session.get('owner'))
    if not owner:
        return jsonify({"message": "Unauthorized access"}), 403
    tickets = []
    for block in reversed(blockchain.chain):
        for transaction in block.transactions:
            # Check if the owner matches in the outputs
            unspent_ticket = blockchain.utxo_pool.get(f"{transaction.tx_id}:0")
            if unspent_ticket is not None and unspent_ticket.public_key_hash == owner:
                # logging.warning(f"transaction.outputs = {output.ticket}")
                tickets.append(unspent_ticket.ticket)
    if not tickets:
        return jsonify({"message": "No tickets found"}), 405
    ticketsData = []
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        for ticket_id in tickets:
            cursor.execute(
                "SELECT * FROM tickets WHERE id = ?", (ticket_id,))
            ticket_data = cursor.fetchone()
            if not ticket_data:
                return "Ticket not found", 404

            ticket = {
                "id": ticket_data[0],
                "event": ticket_data[1],
                "seat": ticket_data[2],
                "price": ticket_data[3],
                "status": ticket_data[4],
            }
            ticketsData.append(ticket)
    return jsonify({"tickets": ticketsData}), 200


@blockchain_bp.route('/get_longest_chain', methods=['GET'])
def get_longest_chain():
    # Return the longest valid chain this node knows about
    return jsonify({"chain": blockchain.get_longest_chain()}), 200
