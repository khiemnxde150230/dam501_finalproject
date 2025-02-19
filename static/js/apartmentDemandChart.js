let chart = null;

async function fetchData() {
    const year = document.getElementById("yearSelect").value;
    const month = document.getElementById("monthSelect").value;

    let url = "/api/apartment-demand";
    let params = [];
    
    if (year) params.push(`year=${year}`);
    if (month) params.push(`month=${month}`);
    
    if (params.length > 0) {
        url += "?" + params.join("&");
    }

    const response = await fetch(url);
    const data = await response.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    const labels = data.sale.map(item => item.district);
    const valuesSale = data.sale.map(item => item.count);
    const valuesRent = data.rent.map(item => item.count);

    const ctx = document.getElementById('apartmentDemandChart').getContext('2d');

    if (chart) {
        chart.destroy();
    }

    chart = new Chart(ctx, {
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

document.getElementById("yearSelect").addEventListener("change", fetchData);
document.getElementById("monthSelect").addEventListener("change", fetchData);

fetchData();