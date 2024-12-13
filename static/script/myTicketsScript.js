
fetch('http://localhost:5000/blockchain/get_my_tickets')
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        const tbody = document.querySelector('tbody');
        tbody.innerHTML = ''; // Clear any existing rows
        data.tickets.forEach(ticket => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="border px-4 py-2">${ticket.id}</td>
                <td class="border px-4 py-2">${ticket.event}</td>
                <td class="border px-4 py-2">${ticket.seat}</td>
                <td class="border px-4 py-2">${ticket.price}</td>
                <td class="border px-4 py-2">${ticket.status}</td>
                <td class="border px-4 py-2"><button class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded" onclick="jualTiket(${ticket.id})">Jual</button></td>
            `;
            tbody.appendChild(row);
        });
    })
    .catch(error => console.error('Error fetching tickets:', error));

function jualTiket(ticketId) {
    window.location.href = `/page/jual/${ticketId}`;
}