function jualTiket(ticketId) {
    // Get the entered price value
    const priceInput = document.getElementById('price');
    const priceSet = priceInput.value;

    if (!priceSet || priceSet <= 0) {
        alert('Please enter a valid price.');
        return;
    }
    // apa kamu yakin ingin menjual tiket ini?
    const confirmation = confirm('Are you sure you want to list this ticket for sale?');
    if (!confirmation) {
        return;
    }
    // Example: Fetch request to sell the ticket
    fetch('/blockchain/sell_ticket', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticket_id: parseInt(ticketId), price: parseInt(priceSet) }), // Send ticket ID and price
    })
    .then(response => {
        if (response.status != 200) {
            return response.json();
        }
        return 200;
    })
    .then(data => {
        if (data == 200) {
            alert('Ticket listed for sale successfully!');
        } else {
            alert('Failed to list ticket for sale: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error listing ticket for sale:', error);
        alert('An error occurred while listing the ticket for sale.');
    });
}

function beliTiket(ticketId){
    // apa kamu yakin ingin membeli tiket ini?
    const confirmation = confirm('Are you sure you want to list this ticket for buy and next to transaction?');
    if (!confirmation) {
        return;
    }
    // Example: Fetch request to sell the ticket
    fetch('/blockchain/buy_ticket', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticket_id: parseInt(ticketId)}), // Send ticket ID and price
    })
    .then(response => {
        if (response.status != 200) {
            return response.json();
        }
        return 200;
    })
    .then(data => {
        if (data == 200) {
            alert('Transaction Created!');
        } else {
            alert('Failed to create transaction: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Failed to create transaction:', error);
        alert('An error occurred while transaction created.');
    });
}
function prosesPembayaran(transactionHash){
    // apa kamu yakin ingin membeli tiket ini?
    const confirmation = confirm('Are you sure you want to pay this transaction?');
    if (!confirmation) {
        return;
    }
    // Example: Fetch request to sell the ticket
    fetch('/blockchain/process_payment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tx_hash: transactionHash}), // Send ticket ID and price
    })
    .then(response => {
        if (response.status != 200) {
            return response.json();
        }
        return 200;
    })
    .then(data => {
        if (data == 200) {
            alert('Transaction Paid!');
        } else {
            alert('Failed to pay transaction: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Failed to pay transaction:', error);
        alert('An error occurred while transaction paid.');
    });
}