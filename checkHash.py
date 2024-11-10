import hashlib
import json


def calculate_hash(index, previous_hash, timestamp, data, nonce):
    block_string = f"{index}{previous_hash}{timestamp}{data}{nonce}"
    print(block_string)
    return hashlib.sha256(block_string.encode('utf-8')).hexdigest()


# Block details from the request
block_data = {
    "data": "Data for node2 mined block",
    "hash": "0000c96e93e81e41b521970b7a830abc75c6a21defb7808ac8ec44625b3b3ffa",
    "index": 5,
    "nonce": 70985,
    "previous_hash": "0000aa68f171d492710b2c07114c9521a7ebfc37848147f3af788ea31bd8d287",
    "timestamp": 1731206662
}


calculated_hash = calculate_hash(
    block_data["index"],
    block_data["previous_hash"],
    block_data["timestamp"],
    block_data["data"],
    block_data["nonce"],
)

print("Calculated Hash:", calculated_hash)
print("Provided Hash:", block_data["hash"])

# Compare if the calculated hash matches the provided hash
is_valid_hash = calculated_hash == block_data["hash"]
is_valid_hash
