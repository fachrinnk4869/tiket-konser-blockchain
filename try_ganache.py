from web3 import Web3
from eth_keys import keys
import json

# Connect to Ethereum node
# Replace with your Ethereum node
web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Check connection
if web3.is_connected():
    print("Connected to Ethereum blockchain")
else:
    print("Connection failed")
    exit()

# Contract details
# Replace with your deployed contract address

# Contract ABI (Paste your ABI here as a string or load from a file)
with open("ticket_abi.json", "r") as abi_file:  # Replace with your ABI JSON file
    contract_abi = json.load(abi_file)

with open("ticket_bin.bin", "r") as bin_file:  # Replace with your ABI JSON file
    # Load Bytecode
    bytecode = bin_file.read().strip()

# Build Contract Deployment
contract = web3.eth.contract(abi=contract_abi, bytecode=bytecode)

# Replace with admin's private key
admin_private_key = "0xedfc17a422af95df6dfdf6f6cf0b7a2c18afa89c5f691d5a24ae645fd01e0ccc"


# public key
admin_account = web3.eth.account.from_key(admin_private_key)
deployer_address = admin_account.address
# Get Nonce
nonce = web3.eth.get_transaction_count(deployer_address)

# Build the Transaction
transaction = contract.constructor().build_transaction({
    'from': deployer_address,
    'nonce': nonce,
    'gas': 1596378,
    'gasPrice': web3.to_wei('10', 'gwei')
})

# Sign the Transaction
signed_txn = web3.eth.account.sign_transaction(
    transaction, admin_private_key)

# Send the Transaction
tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
print(f"Deployment Transaction Hash: {tx_hash.hex()}")

# Wait for the Transaction Receipt
receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
print(f"Contract deployed at address: {receipt.contractAddress}")
# Connect to the smart contract
contract = web3.eth.contract(
    address=receipt.contractAddress, abi=contract_abi)


# Example 1: Issue a new ticket
def issue_ticket(ticket_id, price):
    nonce = web3.eth.get_transaction_count(admin_account.address)
    txn = contract.functions.issueTicket(ticket_id, price).build_transaction({
        'from': admin_account.address,
        'nonce': nonce,
        'gas': 3000000,
        'gasPrice': web3.to_wei('10', 'gwei')
    })

    signed_txn = web3.eth.account.sign_transaction(txn, admin_private_key)
    tx_hash = web3.eth.send_raw_transaction(
        signed_txn.raw_transaction)  # Correct attribute
    print(f"Transaction hash: {tx_hash.hex()}")
    web3.eth.wait_for_transaction_receipt(tx_hash)
    print("Ticket issued successfully")


# Example 2: Create a transaction for a ticket
def create_transaction(ticket_id, buyer_address):
    nonce = web3.eth.get_transaction_count(admin_account.address)
    txn = contract.functions.createTransaction(ticket_id, buyer_address).build_transaction({
        'from': admin_account.address,
        'nonce': nonce,
        'gas': 3000000,
        'gasPrice': web3.to_wei('10', 'gwei')
    })

    signed_txn = web3.eth.account.sign_transaction(txn, admin_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"Transaction hash: {tx_hash.hex()}")
    web3.eth.wait_for_transaction_receipt(tx_hash)
    print("Transaction created successfully")


# Example 3: Process payment
def process_payment(tx_hash, buyer_private_key):
    buyer_account = web3.eth.account.from_key(buyer_private_key)
    tx_data = contract.functions.getTransaction(tx_hash).call()

    nonce = web3.eth.get_transaction_count(buyer_account.address)
    txn = contract.functions.processPayment(tx_hash).build_transaction({
        'from': buyer_account.address,
        'nonce': nonce,
        'value': tx_data[3],  # txData.price
        'gas': 3000000,
        'gasPrice': web3.to_wei('10', 'gwei')
    })

    signed_txn = web3.eth.account.sign_transaction(txn, buyer_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"Transaction hash: {tx_hash.hex()}")
    web3.eth.wait_for_transaction_receipt(tx_hash)
    print("Payment processed successfully")


# Call functions
try:
    # Issue a ticket
    issue_ticket(1, web3.to_wei(1, 'ether'))

    # Create a transaction
    # buyer_address = "0xBuyerAddressHere"  # Replace with buyer's address
    # create_transaction(1, buyer_address)

    # # Process payment
    # transaction_hash = "0xTransactionHashHere"  # Replace with the transaction hash
    # buyer_private_key = "0xBuyerPrivateKeyHere"  # Replace with buyer's private key
    # process_payment(transaction_hash, buyer_private_key)

except Exception as e:
    print(f"An error occurred: {e}")
