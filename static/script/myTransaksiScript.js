    fetch('/smart_contract/get_my_transactions', { method: 'GET' })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch transactions');
                }
                return response.json();
            }
            )
            .then(data => {
                const tbody = document.querySelector('tbody');
        tbody.innerHTML = ''; // Clear any existing rows
        data.transactions.forEach(transaction => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="border px-4 py-2">${transaction.id}</td>
                <td class="border px-4 py-2">${transaction.buyer}</td>
                <td class="border px-4 py-2">${transaction.seller}</td>
                <td class="border px-4 py-2">${transaction.price}</td>
                <td class="border px-4 py-2">${transaction.completed}</td>
                <td class="border px-4 py-2"><button class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded" onclick="prosesPembayaran(this.getAttribute('data-id'))"
                data-id="0x${transaction.hash}")">Bayar</button></td>
            `;
            tbody.appendChild(row);
        });
            })
            .catch(error => console.error('Error fetching transactions:', error));