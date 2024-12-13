// Example JavaScript functions for navbar buttons
function mineBlock() {
    // alert('Mining block...');
    fetch('/blockchain/mine_block', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(response => response.json()).then(data => {
        alert(data.message);
    }).catch(error => console.error('Error mining block:', error));
}


function viewTickets() {
    window.location.href = `/page/mytiket`;
}

function viewMyTransactions() {
    window.location.href = `/page/mytransaksi`;
    
}

function viewBalance() {
    alert('Viewing balance...');
}
// Function to fetch the session user and display it
function displayUserGreeting() {
    fetch('/blockchain/get_user', { method: 'GET' })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch user from session');
            }
            return response.json(); // Parse the JSON response
        })
        .then(data => {
            // Assume the response contains a "username" field
            const username = data.owner || '';
            document.getElementById('greeting').textContent = `Hai, ${username}`;
        })
        .catch(error => {
            console.error('Error fetching user:', error);
            document.getElementById('greeting').textContent = 'Hai,';
        });
}

// Call the function on page load
document.addEventListener('DOMContentLoaded', displayUserGreeting);

function viewBlockChain() {
    fetch('http://localhost:5000/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Remove all existing elements except the navbar
            const mainContent = document.querySelector('.main');
            if (mainContent) {
                mainContent.innerHTML = '';
            }

            const blockchainContainer = document.createElement('div');
            blockchainContainer.className = 'main container mx-auto p-4';

            // Prettify JSON data with indentation and escape characters
            const formattedData = JSON.stringify(data, null, 2);

            blockchainContainer.innerHTML = `
                <h2 class="text-2xl font-bold mb-4">Blockchain Data</h2>
                <pre class="bg-gray-100 p-4 rounded text-sm text-gray-800 whitespace-pre-wrap break-words border border-gray-300">
                    ${formattedData}
                </pre>
            `;
            document.body.appendChild(blockchainContainer);
        })
        .catch(error => console.error('Error fetching blockchain data:', error));
}

function viewUnspentTransactions() {
    fetch('http://localhost:5000/get_utxo_pool')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Remove all existing elements except the navbar
            const mainContent = document.querySelector('.main');
            if (mainContent) {
                mainContent.innerHTML = '';
            }

            const blockchainContainer = document.createElement('div');
            blockchainContainer.className = 'main container mx-auto p-4';

            // Prettify JSON data with indentation and escape characters
            const formattedData = JSON.stringify(data, null, 2);

            blockchainContainer.innerHTML = `
                <h2 class="text-2xl font-bold mb-4">Unspent Transaction Data</h2>
                <pre class="bg-gray-100 p-4 rounded text-sm text-gray-800 whitespace-pre-wrap break-words border border-gray-300">
                    ${formattedData}
                </pre>
            `;
            document.body.appendChild(blockchainContainer);
        })
        .catch(error => console.error('Error fetching Unspent Transaction data:', error));
}
