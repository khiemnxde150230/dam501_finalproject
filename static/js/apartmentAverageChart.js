let chartSale = null;
let chartRent = null;

async function fetchAveragePriceData() {
    const year = document.getElementById("yearSelect").value;
    const month = document.getElementById("monthSelect").value;

    let url = "/api/apartment-average-data";
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

    // Process Sale Data
    const saleLabels = [...new Set(data.average_price_data_sale.map(item => item.year_month))].sort();
    const saleDatasets = {};

    data.average_price_data_sale.forEach(item => {
        if (!saleDatasets[item.bedrooms]) {
            saleDatasets[item.bedrooms] = {
                x: saleLabels,
                y: Array(saleLabels.length).fill(null),
                type: 'scatter',
                mode: 'lines+markers',
                name: `${item.bedrooms} PN`
            };
        }
        const index = saleLabels.indexOf(item.year_month);
        if (index !== -1) {
            saleDatasets[item.bedrooms].y[index] = item.avg_price;
        }
    });

    const saleDataPlotly = Object.values(saleDatasets);

    const layoutSale = {
        title: 'Giá trung bình căn hộ bán theo tháng',
        xaxis: { title: 'Tháng' },
        yaxis: { title: 'Giá trung bình (VND)' }
    };

    if (chartSale) {
        Plotly.react('apartmentSaleChart', saleDataPlotly, layoutSale);
    } else {
        chartSale = Plotly.newPlot('apartmentSaleChart', saleDataPlotly, layoutSale);
    }

    // Process Rent Data
    const rentLabels = [...new Set(data.average_price_data_rent.map(item => item.year_month))].sort();
    const rentDatasets = {};

    data.average_price_data_rent.forEach(item => {
        if (!rentDatasets[item.bedrooms]) {
            rentDatasets[item.bedrooms] = {
                x: rentLabels,
                y: Array(rentLabels.length).fill(null),
                type: 'scatter',
                mode: 'lines+markers',
                name: `${item.bedrooms} PN`
            };
        }
        const index = rentLabels.indexOf(item.year_month);
        if (index !== -1) {
            rentDatasets[item.bedrooms].y[index] = item.avg_price;
        }
    });

    const rentDataPlotly = Object.values(rentDatasets);

    const layoutRent = {
        title: 'Giá trung bình căn hộ thuê theo tháng',
        xaxis: { title: 'Tháng' },
        yaxis: { title: 'Giá trung bình (VND)' }
    };

    if (chartRent) {
        Plotly.react('apartmentRentChart', rentDataPlotly, layoutRent);
    } else {
        chartRent = Plotly.newPlot('apartmentRentChart', rentDataPlotly, layoutRent);
    }
}

// Add event listeners for filters
document.getElementById("yearSelect").addEventListener("change", fetchAveragePriceData);
document.getElementById("monthSelect").addEventListener("change", fetchAveragePriceData);

// Initial data fetch
fetchAveragePriceData();
