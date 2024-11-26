from flask import Blueprint, jsonify, request
from flask_bcrypt import Bcrypt
import sqlite3
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import uuid
import os

# SQLite database path
DATABASE = 'tickets.db'

# Initialize Flask Blueprint
auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()
KEYS_DIR = 'keys'  # Directory to store the keys
os.makedirs(KEYS_DIR, exist_ok=True)  # Create directory if it doesn't exist
# Initialize database if not exists
owner = None

# Example route for registration


def init_db():

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS tickets (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            event TEXT,
                            seat TEXT,
                            status TEXT
                        )''')  # Status: "jual" or "beli"
        cursor.execute('''CREATE TABLE IF NOT EXISTS tokens (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            token TEXT,
                            ticket_id TEXT
                        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL
                        )''')  # Stores hashed passwords
        # Check if the tickets table is empty
        cursor.execute('SELECT COUNT(*) FROM tickets')
        if cursor.fetchone()[0] == 0:
            # Add 10 tickets to the tickets table
            tickets = [
                ('Concert A', 'A1', 'jual'),
                ('Concert A', 'A2', 'jual'),
                ('Concert A', 'A3', 'jual'),
                ('Concert A', 'A4', 'jual'),
                ('Concert A', 'A5', 'jual'),
                ('Concert B', 'B1', 'jual'),
                ('Concert B', 'B2', 'jual'),
                ('Concert B', 'B3', 'jual'),
                ('Concert B', 'B4', 'jual'),
                ('Concert B', 'B5', 'jual')
            ]
            cursor.executemany(
                'INSERT INTO tickets (event, seat, status) VALUES (?, ?, ?)', tickets)
        conn.commit()


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        try:
            # Insert the user into the database
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()

            # Generate RSA keys for the user
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            public_key = private_key.public_key()

            # Serialize and save private key
            private_key_path = os.path.join(
                KEYS_DIR, f'private_{username}.pem')
            with open(private_key_path, 'wb') as private_file:
                private_file.write(
                    private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.TraditionalOpenSSL,
                        encryption_algorithm=serialization.NoEncryption()
                    )
                )

            # Serialize and save public key
            public_key_path = os.path.join(KEYS_DIR, f'public_{username}.pem')
            with open(public_key_path, 'wb') as public_file:
                public_file.write(
                    public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    )
                )

            return jsonify({"message": "User registered successfully"}), 201

        except sqlite3.IntegrityError:
            return jsonify({"message": "Username already exists"}), 409

# Example route for login


@auth_bp.route('/login', methods=['POST'])
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
            global owner
            owner = username
            return jsonify({"message": "Login successful"}), 200
        return jsonify({"message": "Invalid username or password"}), 401


@auth_bp.route('/logout', methods=['POST'])
def logout():
    global owner
    owner = None
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route('/get_user', methods=['GET'])
def get_user():
    return jsonify({"owner": owner}), 200
