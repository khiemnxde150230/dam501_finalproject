async function fetchData() {
    const response = await fetch('/api/apartment-demand');
    const data = await response.json();

    const labels = data.sale.map(item => item.district);
    const valuesSale = data.sale.map(item => item.count);
    const valuesRent = data.rent.map(item => item.count);

    new Chart(document.getElementById('apartmentDemandChart').getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Bán',
                    data: valuesSale,
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                },
                {
                    label: 'Cho Thuê',
                    data: valuesRent,
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                }
            ]
        },
        options: { responsive: true }
    });
}

fetchData();