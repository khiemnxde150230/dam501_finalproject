let chartPricePerSqm = null;
let currentMode = "sale"; // Default mode

async function fetchDistricts() {
    const response = await fetch('/api/available-districts');
    const data = await response.json();

    const districtSelect = document.getElementById("districtSelect");
    districtSelect.innerHTML = `<option value="">Tất cả Quận</option>`;
    data.districts.forEach(district => {
        const option = document.createElement("option");
        option.value = district;
        option.textContent = district;
        districtSelect.appendChild(option);
    });
}

async function fetchPricePerSqmData() {
    const year = document.getElementById("yearSelect").value;
    const month = document.getElementById("monthSelect").value;
    const district = document.getElementById("districtSelect").value;

    let url = currentMode === "sale" ? "/api/average-sale-price-per-sqm" : "/api/average-rent-price-per-sqm";
    let params = [];

    if (year) params.push(`year=${year}`);
    if (month) params.push(`month=${month}`);
    if (district) params.push(`district=${encodeURIComponent(district)}`);

    if (params.length > 0) {
        url += "?" + params.join("&");
    }

    const response = await fetch(url);
    const data = await response.json();

    const key = currentMode === "sale" ? "average_price_data_sale" : "average_price_data_rent";
    const fetchedData = data[key];

    if (!fetchedData || fetchedData.length === 0) {
        alert("Không có dữ liệu.");
        return;
    }

    // Process data for the column chart
    const months = [...new Set(fetchedData.map(item => item.year_month))].sort();
    const avgPrices = months.map(m => {
        const record = fetchedData.find(item => item.year_month === m);
        return record ? record.avg_price : null;
    });

    const chartData = [{
        x: months,
        y: avgPrices,
        type: 'bar',
        marker: { color: currentMode === "sale" ? 'rgba(255, 99, 132, 0.7)' : 'rgba(54, 162, 235, 0.7)' }
    }];

    const layout = {
        title: currentMode === "sale" ? `Giá trung bình mỗi m² bán theo tháng (${district || "Tất cả Quận"})`
                                       : `Giá trung bình mỗi m² thuê theo tháng (${district || "Tất cả Quận"})`,
        xaxis: { title: "Tháng" },
        yaxis: { title: "Giá trung bình (VND/m²)" },
        barmode: 'group'
    };

    if (chartPricePerSqm) {
        Plotly.react("apartmentPricePerSqmChart", chartData, layout);
    } else {
        chartPricePerSqm = Plotly.newPlot("apartmentPricePerSqmChart", chartData, layout);
    }
}

// Function to switch between Sale and Rent modes
function switchMode(mode) {
    currentMode = mode;
    document.getElementById("saleBtn").classList.toggle("btn-primary", mode === "sale");
    document.getElementById("saleBtn").classList.toggle("btn-outline-primary", mode !== "sale");
    document.getElementById("rentBtn").classList.toggle("btn-primary", mode === "rent");
    document.getElementById("rentBtn").classList.toggle("btn-outline-primary", mode !== "rent");

    fetchPricePerSqmData();
}

// Event listeners
document.getElementById("yearSelect").addEventListener("change", fetchPricePerSqmData);
document.getElementById("monthSelect").addEventListener("change", fetchPricePerSqmData);
document.getElementById("districtSelect").addEventListener("change", fetchPricePerSqmData);
document.getElementById("saleBtn").addEventListener("click", () => switchMode("sale"));
document.getElementById("rentBtn").addEventListener("click", () => switchMode("rent"));

// Fetch districts and initial data
fetchDistricts();
fetchPricePerSqmData();
