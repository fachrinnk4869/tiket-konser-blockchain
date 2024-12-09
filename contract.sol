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

    event TicketIssued(uint256 indexed ticketId, address indexed owner, uint256 price);
    event TransactionCreated(uint256 indexed ticketId, address indexed buyer, address indexed seller, uint256 price, bytes32 hash);
    event PaymentProcessed(uint256 indexed ticketId, address indexed buyer, address indexed seller, uint256 price);

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action");
        _;
    }

    modifier onlyTicketOwner(uint256 ticketId) {
        require(tickets[ticketId].owner == msg.sender, "You are not the ticket owner");
        _;
    }

    constructor() {
        admin = msg.sender;
    }

    function issueTicket(uint256 ticketId, uint256 price) external onlyAdmin {
        require(tickets[ticketId].owner == address(0), "Ticket already exists");
        tickets[ticketId] = Ticket(ticketId, admin, price, true);
        emit TicketIssued(ticketId, admin, price);
    }

    function createTransaction(uint256 ticketId, address buyer) external {
        Ticket memory ticket = tickets[ticketId];
        require(ticket.isAvailable, "Ticket is not available");
        require(ticket.owner == msg.sender, "Only the owner can sell this ticket");

        bytes32 txHash = keccak256(abi.encodePacked(ticketId, buyer, msg.sender, ticket.price, block.timestamp));
        transactions[txHash] = Transaction(ticketId, buyer, msg.sender, ticket.price, false, txHash);

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
}
