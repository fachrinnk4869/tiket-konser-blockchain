from flask import Flask, jsonify, request
from blockchain import Block, Blockchain, Transaction
import requests
from flask import Flask, request, jsonify
from wallet import Owner, Transaction
from flask_bcrypt import Bcrypt
from transaction.transaction_input import TransactionInput
from transaction.transaction_output import TransactionOutput
import sqlite3
import uuid
from route.auth import auth_bp, init_db, owner
from route.blockchain_transaction import blockchain_bp, blockchain


# SQLite database path
DATABASE = 'tickets.db'

# Initialize database if not exists


app = Flask(__name__)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(blockchain_bp, url_prefix='/blockchain')


init_db()


@app.route('/', methods=['GET'])
def get_blockchain():
    return jsonify(blockchain.get_chain())


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
