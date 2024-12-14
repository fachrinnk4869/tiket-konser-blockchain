import logging
from flask import Blueprint, jsonify, request,  session
from flask_bcrypt import Bcrypt
import sqlite3
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import uuid
import os
import requests
from wallet import Owner
from web3 import Web3
# SQLite database path
DATABASE = 'tickets.db'

# Initialize Flask Blueprint
auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()
KEYS_DIR = 'keys'  # Directory to store the keys
os.makedirs(KEYS_DIR, exist_ok=True)  # Create directory if it doesn't exist
# Initialize database if not exists

# Example route for registration


def init_db():

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS tickets (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            event TEXT,
                            seat TEXT,
                            price INTEGER,
                            status TEXT,
                            sign TEXT
                        )''')  # Status: "jual" or "beli"
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL,
                            role TEXT NOT NULL
                        )''')  # Stores hashed passwords
        cursor.execute("""CREATE TABLE IF NOT EXISTS transactions (
                            id INTEGER PRIMARY KEY,
                            ticket_id TEXT,
                            hash TEXT
                        )""")
        conn.commit()


w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))


@ auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        try:
            # Insert the user into the database
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_password, role))
            conn.commit()

            # Generate a new Ethereum account
            account = w3.eth.account.create()

            # Print account details
            print(f"New User Registered:")
            print(f"Address: {account.address}")
            print(f"Private Key: {account._private_key.hex()}")

            # Define file paths for saving the public and private keys
            public_file_path = f"./keys/public_{username}.pem"
            private_file_path = f"./keys/private_{username}.pem"

            # Save the public key to a text file
            with open(public_file_path, 'w') as public_file:
                public_file.write(account.address)
            print(f"Public key saved to {public_file_path}")

            # Save the private key to a text file
            with open(private_file_path, 'w') as private_file:
                private_file.write(account._private_key.hex())
            print(f"Private key saved to {private_file_path}")
            # Address of the account whose balance you want to check
            address = account.address
            # Check balance of a pre-existing account (usually account 0 in Ganache)
            from_account = w3.eth.accounts[0]

            # Send 100 ETH to the newly created account
            tx_hash = w3.eth.send_transaction({
                'from': from_account,
                'to': address,
                'value': w3.to_wei(90, 'ether'),
                'gas': 2000000,
                'gasPrice': w3.to_wei('20', 'gwei')
            })

            # Wait for the transaction to be mined
            w3.eth.wait_for_transaction_receipt(tx_hash)

            # Check the balance of the newly created account
            balance_wei = w3.eth.get_balance(address)

            # Convert balance from Wei to Ether (1 Ether = 1e18 Wei)
            return jsonify({"message": f"User {username} registered successfully", "balance(eth)": balance_wei}), 201

        except sqlite3.IntegrityError:
            return jsonify({"message": "Username already exists"}), 409

# Example route for login


@ auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user[0], password):
            session['owner'] = username  # Set session for the user
            return jsonify({"message": "Login successful"}), 200
        return jsonify({"message": "Invalid username or password"}), 401


@auth_bp.route('/get_balance', methods=['GET'])
def get_balance():
    username = session.get('owner')
    if not username:
        return jsonify({"message": "Unauthorized"}), 401

    address = Owner.get_public_key(username)
    balance_wei = w3.eth.get_balance(address)
    # Convert balance from Wei to Ether (1 Ether = 1e18 Wei)
    balance = w3.from_wei(balance_wei, 'ether')
    return jsonify({"balance(eth)": balance}), 200


@ auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('owner')
    return jsonify({"message": "Logged out successfully"}), 200
