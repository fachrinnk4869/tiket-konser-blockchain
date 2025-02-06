from wallet import Owner
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
usernames = ['admin', 'user', 'user1', 'user2']
for username in usernames:
    address = Owner.get_public_key(username)
    balance_wei = w3.eth.get_balance(address)
    # Convert balance from Wei to Ether (1 Ether = 1e18 Wei)
    balance = w3.from_wei(balance_wei, 'ether')
    print(f"Username: {username}, Balance: {balance}")
