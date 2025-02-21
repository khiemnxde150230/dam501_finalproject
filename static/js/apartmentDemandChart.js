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

    const traceSale = {
        x: labels,
        y: valuesSale,
        type: 'bar',
        name: 'Bán',
        marker: {
            color: 'rgba(255, 99, 132, 0.6)'
        }
    };

    const traceRent = {
        x: labels,
        y: valuesRent,
        type: 'bar',
        name: 'Cho Thuê',
        marker: {
            color: 'rgba(54, 162, 235, 0.6)'
        }
    };

    const dataPlotly = [traceSale, traceRent];

    const layout = {
        title: 'Số lượng tin cho thuê/bán theo quận',
        barmode: 'group',
        xaxis: {
            title: 'Quận'
        },
        yaxis: {
            title: 'Số lượng'
        }
    };

    if (chart) {
        Plotly.react('apartmentDemandChart', dataPlotly, layout);
    } else {
        chart = Plotly.newPlot('apartmentDemandChart', dataPlotly, layout);
    }
}

document.getElementById("yearSelect").addEventListener("change", fetchData);
document.getElementById("monthSelect").addEventListener("change", fetchData);

fetchData();