# Scratch Code

curl -X POST -H "Content-Type: application/json" -d '{"sender": "Alice", "receiver": "Bob", "amount": 10}' http://localhost:5001/add_transaction

curl -X POST http://localhost:5002/mine_block

curl -X POST http://localhost:5001/crash_block -H "Content-Type: application/json" -d '{
  "block": {
    "index": 1,
    "transactions": [
      {
        "sender": "Alice",
        "receiver": "Bob",
        "amount": 0
      }
    ]
  }
}'

curl -X POST http://localhost:5002/mine_block

curl -X POST http://localhost:5001/fix_blockchain