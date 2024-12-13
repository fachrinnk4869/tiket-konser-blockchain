from dotenv import load_dotenv
import logging
from flask import Flask, request, jsonify, session
import requests
from web3 import Web3
import json
from flask import Blueprint, jsonify, request, session
from wallet import Owner
import os

# SQLite database path
DATABASE = 'tickets.db'

# Initialize Flask Blueprint
smart_contract_bp = Blueprint('smart_contract', __name__)
# Connect to Ethereum node
ganache_url = "http://127.0.0.1:8545"
web3 = Web3(Web3.HTTPProvider(ganache_url))

# Check connection
if not web3.is_connected():
    raise Exception("Unable to connect to Ganache")

# Load Contract ABI and Bytecode
with open("ticket_abi.json", "r") as abi_file:
    contract_abi = json.load(abi_file)

with open("ticket_bin.bin", "r") as bin_file:
    contract_bytecode = bin_file.read().strip()

# Private Key and Address (Admin Account)
# Replace with your private key
load_dotenv()
try:

    # Load environment variables from .env file

    # Access the smart contract address
    contract_address = os.getenv("SMART_CONTRACT_ADDRESS")
except Exception as e:
    response = requests.post(
        "http://localhost:5000/smart_contract/deploy_smart_contract")
    contract_address = response.json()['contract_address']
    logging.warning(f"Contract Address: {contract_address}")
# Access contract
contract_instance = web3.eth.contract(
    address=contract_address, abi=contract_abi)
logging.warning(contract_instance)


@smart_contract_bp.route('/deploy_smart_contract', methods=['POST'])
def deploy_contract():
    try:
        global contract_instance
        global contract_address
        data = request.json
        user_private_key = Owner.get_private_key(
            session.get('owner', None), import_key=False)
        user_account = web3.eth.account.from_key(user_private_key)
        user_address = user_account.address

        # Deploy contract
        contract = web3.eth.contract(
            abi=contract_abi, bytecode=contract_bytecode)
        nonce = web3.eth.get_transaction_count(user_address)
        transaction = contract.constructor().build_transaction({
            'from': user_address,
            'nonce': nonce,
            'gas': 3000000,
            'gasPrice': web3.to_wei('10', 'gwei')
        })
        signed_txn = web3.eth.account.sign_transaction(
            transaction, user_private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        contract_address = receipt.contractAddress
        contract_instance = web3.eth.contract(
            address=contract_address, abi=contract_abi)
        return jsonify({"message": "Contract deployed successfully", "contract_address": contract_address})
    except Exception as e:
        logging.error(e)
        return jsonify({"error": str(e)}), 500


@smart_contract_bp.route('/access_deployed_contract', methods=['POST'])
def access_deployed_contract():
    try:
        global contract_instance
        data = request.json
        contract_address = data['contract_address']

        # Access contract
        contract_instance = web3.eth.contract(
            address=contract_address, abi=contract_abi)
        logging.warning(contract_instance)
        return jsonify({"message": "Contract accessed successfully", "contract_address": contract_address})
    except Exception as e:
        logging.error(e)
        return jsonify({"error": str(e)}), 500


@smart_contract_bp.route('/')
def index():
    return jsonify({"message": "Smart Contract API is running", "contract_address": contract_address})


@smart_contract_bp.route('/issue_ticket', methods=['POST'])
def issue_ticket():
    try:
        data = request.json
        ticket_id = data['ticket_id']
        owner = data.get('owner', None)
        if not owner:
            owner = session.get('owner')
        price = data['price']
        user_private_key = Owner.get_private_key(
            owner, import_key=False)
        user_account = web3.eth.account.from_key(user_private_key)
        user_address = user_account.address

        nonce = web3.eth.get_transaction_count(user_address)
        txn = contract_instance.functions.issueTicket(ticket_id, price).build_transaction({
            'from': user_address,
            'nonce': nonce,
            'gas': 3000000,
            'gasPrice': web3.to_wei('10', 'gwei')
        })
        signed_txn = web3.eth.account.sign_transaction(txn, user_private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        logging.warning(f"signed transaction: {signed_txn.hash.hex()}")
        return jsonify({"message": "Ticket issued successfully", "transaction_hash": tx_hash.hex(), "signature": f"0x{signed_txn.hash.hex()}"})
    except Exception as e:
        # If the error has a `data` attribute (check first), log it
        if hasattr(e, 'data'):
            logging.error(f"Error data: {e.data}")
        return jsonify({"error": str(e)}), 500


@smart_contract_bp.route('/create_transaction', methods=['POST'])
def create_transaction():
    try:
        data = request.json
        ticket_id = data['ticket_id']
        owner = data.get('owner', None)
        if not owner:
            owner = session.get('owner')
        buyer_address = Owner.get_public_key(owner)
        user_private_key = Owner.get_private_key(
            owner, import_key=False)
        user_account = web3.eth.account.from_key(user_private_key)
        user_address = user_account.address

        nonce = web3.eth.get_transaction_count(user_address)
        txn = contract_instance.functions.createTransaction(ticket_id, buyer_address).build_transaction({
            'from': user_address,
            'nonce': nonce,
            'gas': 3000000,
            'gasPrice': web3.to_wei('10', 'gwei')
        })
        signed_txn = web3.eth.account.sign_transaction(txn, user_private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        # Wait for the transaction receipt
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        # Decode the returned value (transaction hash)
        logs = contract_instance.events.TransactionCreated().process_receipt(receipt)
        for log in logs:
            returned_tx_hash = log.args.hash
            logging.warning(
                f"Returned Transaction Hash: 0x{returned_tx_hash.hex()}")

        return jsonify({"message": "Transaction created successfully", "transaction_hash": f"0x{returned_tx_hash.hex()}"})
    except Exception as e:
        logging.error(e)
        return jsonify({"error": str(e)}), 500


@smart_contract_bp.route('/process_payment', methods=['POST'])
def process_payment():
    try:
        data = request.json
        tx_hash = data['tx_hash']
        owner = data.get('owner', None)
        if not owner:
            owner = session.get('owner')
        buyer_private_key = Owner.get_private_key(
            owner, import_key=False)
        buyer_account = web3.eth.account.from_key(buyer_private_key)

        tx_data = contract_instance.functions.getTransaction(tx_hash).call()
        price = tx_data[3]
        logging.warning(f"Price: {price}")
        # Assuming tx_data[1] contains the seller's address
        seller_address = tx_data[1]
        logging.warning(f"Seller Address: {seller_address}")

        if not seller_address:
            return jsonify({"error": "Seller address not found"}), 400

        nonce = web3.eth.get_transaction_count(buyer_account.address)
        txn = contract_instance.functions.processPayment(tx_hash).build_transaction({
            'from': buyer_account.address,
            'nonce': nonce,
            'value': price,
            'gas': 3000000,
            'gasPrice': web3.to_wei('10', 'gwei')
        })

        signed_txn = web3.eth.account.sign_transaction(txn, buyer_private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        return jsonify({"message": "Payment processed successfully", "transaction_hash": tx_hash.hex(), "price": price, "ticket_id": tx_data[0]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@smart_contract_bp.route('/get_my_transactions', methods=['GET'])
def get_my_transactions():
    user_address = Owner.get_public_key(session.get('owner', None))
    try:
        transactions = contract_instance.functions.getTransactionsByUser(
            user_address).call()
    except Exception as e:
        print(f"Error fetching transactions: {e}")
    transactionsData = []
    for tx in transactions:
        ticket = {
            "id": tx[0],
            "buyer": tx[1],
            "seller": tx[2],
            "price": tx[3],
            "completed": tx[4],
            "hash": tx[5].hex()  # Convert bytes to hex string
        }
        transactionsData.append(ticket)
    return jsonify({"transactions": transactionsData}), 200


if __name__ == '__main__':
    smart_contract_bp.run(debug=True, port=5000)
