from route.blockchain_transaction import blockchain_bp, blockchain
from route.auth import auth_bp, init_db
import sqlite3
from flask import Flask, jsonify, request, session
from flask_cors import CORS

from wallet import Owner

# SQLite database path
DATABASE = 'tickets.db'

# Initialize database if not exists


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['SECRET_KEY'] = 'super_secure'
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(blockchain_bp, url_prefix='/blockchain')
init_db()


@app.route('/get_user', methods=['GET'])
def get_user():
    owner = session.get('owner')
    return jsonify({"owner": owner}), 200


@app.route('/', methods=['GET'])
def get_blockchain():
    return jsonify(blockchain.get_chain())


@app.route("/get_utxo_pool", methods=["GET"])
def get_utxo_pool():
    utxo_pool = blockchain.get_utxo_pool()
    return jsonify(utxo_pool), 200


@app.route("/get_balance", methods=["GET"])
def get_balance():
    owner = Owner.get_public_key(session.get('owner', None))
    balance = blockchain.get_balance(owner)
    return jsonify({"balance": balance}), 200


@app.route("/get_tickets", methods=["GET"])
def get_tickets():
    owner = Owner.get_public_key(session.get('owner', None))
    tickets = blockchain.get_tickets(owner)
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        ticket_list = []
        for ticket in tickets:
            cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket,))
            ticket_data = cursor.fetchone()
            ticket_data = {
                "id": ticket_data[0],
                "event": ticket_data[1],
                "seat": ticket_data[2],
                "price": ticket_data[3],
                "status": ticket_data[4],
            }
            ticket_list.append(ticket_data)
    return jsonify(ticket_list), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
