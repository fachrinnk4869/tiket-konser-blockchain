from web3 import Web3
from eth_account.messages import encode_defunct

# Connect to Ethereum node (e.g., Ganache)
ganache_url = "http://127.0.0.1:8545"
web3 = Web3(Web3.HTTPProvider(ganache_url))

# Example private key and corresponding public address
private_key = "0x315a9dac683c5a6c0d2fff5392c105694ad9909f60da4f570a28f5d4fd1699a4"
public_address = web3.eth.account.from_key(private_key).address

# Message to sign
message = "This is a test message for signing and validation."

# Step 1: Sign the message
# Encode the message
encoded_message = encode_defunct(text=message)
# encoded_message = message.encode('utf-8')

# Sign the encoded message with the private key
signed_message = web3.eth.account.sign_message(encoded_message, private_key)
print(f"Signed Message: {signed_message}")

# Signature details
signature = f"{signed_message.signature.hex()}"
print(f"Signature (hex): {signature}")


# Step 2: Validate the signature
# Recover the address from the signature
recovered_address = web3.eth.account.recover_message(
    encoded_message, signature=signature)
print(f"Recovered Address: {recovered_address}")

# Check if the recovered address matches the public address
if recovered_address == public_address:
    print("Signature is valid! The signer owns the private key.")
else:
    print("Signature is invalid!")
