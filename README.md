
# Blockchain Project with Docker and 3 Nodes

Project Presentation: [Project Presentation](https://docs.google.com/presentation/d/1-aFvEs3amtuCFr3_-DdB4Lt2NylausSzSibgRffqtrc/edit?usp=sharing)

This project demonstrates a basic blockchain implementation using Flask for API endpoints and Docker for containerized multi-node support. We’ll set up a network of three nodes to simulate interactions between distributed blockchain nodes.

## Setup

### Prerequisites

- **Docker**: Ensure Docker is installed on your system.

### Running the Docker Network

1. Clone the repository:

   ```bash
   git clone https://github.com/fachrinnk4869/tiket-konser-blockchain
   cd tiket-konser-blockchain

   ```

2. Start the Docker containers for the three nodes:

   ```bash
   docker compose up --build
   ```

   This command creates and starts three separate nodes (`node1`, `node2`, and `node3`) on ports `5001`, `5002`, and `5003`, respectively.

3. Confirm that the nodes are running by checking the Docker logs:

   ```bash
   docker compose logs -f
   ```

### Endpoints

Below is a list of the main endpoints you can interact with:

1. **Add a Transaction**  
   Adds a transaction to the pending transaction list on a specific node.

   ```http
   POST /add_transaction
   ```

   - **Data**:
     ```json
     {
       "sender": "Alice",
       "receiver": "Bob",
       "amount": 10
     }
     ```
   - **Example**:
     ```bash
     curl -X POST -H "Content-Type: application/json" -d '{"sender": "Alice", "receiver": "Bob", "amount": 10}' http://localhost:5001/add_transaction
     ```

2. **Mine a Block**  
   Mines a new block on the blockchain for the node that receives the request.

   ```http
   POST /mine_block
   ```

   - **Example**:
     ```bash
     curl -X POST http://localhost:5001/mine_block
     ```

3. **Crash a Block**  
   Alters the contents of a block at a specified index to simulate a data crash or tampering.

   ```http
   POST /crash_block
   ```

   - **Data**:
     ```json
     {
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
     }
     ```
   - **Example**:
     ```bash
     curl -X POST http://localhost:5001/crash_block -H "Content-Type: application/json" -d '{
       "block": {
         "index": 1,
         "transactions": [
           {
             "sender": "Alice",
             "receiver": "Bob",
             "seat": "Bob",
             "event": "Bob",
             "amount": 0
           }
         ]
       }
     }'
     ```

4. **Fix Blockchain**  
   Compares and replaces the local chain with the longest valid chain from other nodes if the local chain is corrupted.

   ```http
   POST /fix_blockchain
   ```

   - **Example**:
     ```bash
     curl -X POST http://localhost:5001/fix_blockchain
     ```

### Demo

To demonstrate the functionality, use the following steps:

1. **Add a Transaction**: Add a new transaction to `node1`.
   ```bash
   curl -X POST -H "Content-Type: application/json" -d '{"sender": "Alice", "receiver": "Bob", "amount": 10}' http://localhost:5001/add_transaction
   ```

2. **Mine a Block**: Mine a new block on `node1`.
   ```bash
   curl -X POST http://localhost:5001/mine_block
   ```

3. **Crash a Block**: Modify a block in `node1` to simulate data tampering.
   ```bash
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
   ```

4. **Mine a Block on Another Node**: Mine a new block on `node2` to confirm the chain continues.
   ```bash
   curl -X POST http://localhost:5002/mine_block
   ```

5. **Fix the Chain**: Use the `fix_blockchain` endpoint to repair the tampered chain on `node1`.
   ```bash
   curl -X POST http://localhost:5001/fix_blockchain
   ```

This sequence showcases a typical workflow for adding, modifying, and recovering the blockchain state across nodes.

### Additional Notes

- **Network Setup**: Docker Compose handles networking automatically. Each node runs in its own container and communicates via internal Docker networking.
- **Logs**: To view detailed logs for debugging or monitoring purposes, run `docker compose logs -f`.

### Stopping the Network

To stop and remove the Docker containers, use:

```bash
docker compose down
```
