
# Ticketing Smart Contract Blockchain

Project Presentation: [Project Presentation](https://docs.google.com/presentation/d/1mVsFcYpO-7IKwj4GLoTrnK8p_2PQxy2RlsX6sXDWBvs/edit?usp=sharing)

This project demonstrates a blockchain and smart contract implementation using Flask for API endpoints and Docker for containerized multi-node support.

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

3. Confirm that the nodes are running by checking the Docker logs:

   ```bash
   docker compose logs -f
   ```
### Interface

### Flow
![image](https://github.com/user-attachments/assets/26eefc63-460d-4832-95bd-48331abd9471)


### Additional Notes

- **Network Setup**: Docker Compose handles networking automatically. Each node runs in its own container and communicates via internal Docker networking.
- **Logs**: To view detailed logs for debugging or monitoring purposes, run `docker compose logs -f`.

### Stopping the Network

To stop and remove the Docker containers, use:

```bash
docker compose down
```
