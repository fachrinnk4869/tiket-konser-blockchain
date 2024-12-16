// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TicketMarketplace {
    address public admin;

    struct Ticket {
        uint256 id;
        address owner;
        uint256 price;
        bool isAvailable;
    }

    struct Transaction {
        uint256 ticketId;
        address buyer;
        address seller;
        uint256 price;
        bool isCompleted;
        bytes32 hash;
    }

    mapping(uint256 => Ticket) public tickets;
    mapping(bytes32 => Transaction) public transactions;
    uint256[] private ticketIds;
    bytes32[] private transactionHashes;

    event TicketIssued(uint256 indexed ticketId, address indexed owner, uint256 price);
    event TransactionCreated(uint256 indexed ticketId, address indexed buyer, address indexed seller, uint256 price, bytes32 hash);
    event PaymentProcessed(uint256 indexed ticketId, address indexed buyer, address indexed seller, uint256 price);

    function issueTicket(uint256 ticketId, uint256 price) external {
        Ticket storage ticket = tickets[ticketId];

        if (ticket.owner == address(0)) {
            // First-time issuance
            tickets[ticketId] = Ticket(ticketId, msg.sender, price, true);
            ticketIds.push(ticketId);
            emit TicketIssued(ticketId, msg.sender, price);
        } else {
            // Re-issuing an existing ticket
            require(ticket.owner == msg.sender, "Only the owner can make the ticket available");
            require(!ticket.isAvailable, "Ticket is already available");

            ticket.isAvailable = true;
            ticket.price = price;
            emit TicketIssued(ticketId, msg.sender, price);
        }

    }

    function createTransaction(uint256 ticketId, address buyer) external {
        Ticket memory ticket = tickets[ticketId];
        require(ticket.isAvailable, "Ticket is not available");
        require(ticket.owner != msg.sender, "The owner can't buy this ticket");

        bytes32 txHash = keccak256(abi.encodePacked(ticketId, buyer, ticket.owner, ticket.price, block.timestamp));
        transactions[txHash] = Transaction(ticketId, buyer, ticket.owner, ticket.price, false, txHash);
        transactionHashes.push(txHash);

        emit TransactionCreated(ticketId, buyer, msg.sender, ticket.price, txHash);
    }

    function processPayment(bytes32 txHash) external payable {
        Transaction storage txData = transactions[txHash];
        require(!txData.isCompleted, "Transaction already completed");
        require(msg.value >= txData.price, "Insufficient payment");
        require(txData.buyer == msg.sender, "Buyer is not recognized");

        Ticket storage ticket = tickets[txData.ticketId];
        require(ticket.isAvailable, "Ticket is no longer available");

        // Transfer payment to seller
        payable(txData.seller).transfer(txData.price);

        // Update ticket ownership
        ticket.owner = txData.buyer;
        ticket.isAvailable = false;

        // Mark transaction as completed
        txData.isCompleted = true;

        emit PaymentProcessed(txData.ticketId, txData.buyer, txData.seller, txData.price);
    }

    function getTicket(uint256 ticketId) external view returns (Ticket memory) {
        return tickets[ticketId];
    }

    function getTransaction(bytes32 txHash) external view returns (Transaction memory) {
        return transactions[txHash];
    }

    function getTicketsByUser(address user) external view returns (Ticket[] memory) {
        uint256 count = 0;
        for (uint256 i = 0; i < ticketIds.length; i++) {
            if (tickets[ticketIds[i]].owner == user) {
                count++;
            }
        }

        Ticket[] memory userTickets = new Ticket[](count);
        uint256 index = 0;
        for (uint256 i = 0; i < ticketIds.length; i++) {
            if (tickets[ticketIds[i]].owner == user) {
                userTickets[index] = tickets[ticketIds[i]];
                index++;
            }
        }
        return userTickets;
    }

    function getTransactionsByUser(address user) external view returns (Transaction[] memory) {
        uint256 count = 0;
        for (uint256 i = 0; i < transactionHashes.length; i++) {
            Transaction memory txData = transactions[transactionHashes[i]];
            if (txData.buyer == user || txData.seller == user) {
                count++;
            }
        }

        Transaction[] memory userTransactions = new Transaction[](count);
        uint256 index = 0;
        for (uint256 i = 0; i < transactionHashes.length; i++) {
            Transaction memory txData = transactions[transactionHashes[i]];
            if (txData.buyer == user || txData.seller == user) {
                userTransactions[index] = txData;
                index++;
            }
        }
        return userTransactions;
    }
}
