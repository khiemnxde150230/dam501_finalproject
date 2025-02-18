async function fetchData() {
    const response = await fetch("/api/apartment-area-selling", {
        headers: { "Accept": "application/json" }  // ✅ Ensure JSON response
    });
    const data = await response.json();
    console.log(data)
    const districts = Object.keys(data);
    const areaGroups = ["<30", "30-50", "50-100", ">100"];
    
    const dataset = areaGroups.map(group => ({
        label: group,
        data: districts.map(district => data[district][group] || 0),
        backgroundColor: getColor(group),
    }));

    new Chart(document.getElementById("apartment_area_selling_chart"), {
        type: "bar",
        data: {
            labels: districts,
            datasets: dataset
        },
        options: { responsive: true }
    });
}

function getColor(group) {
    const colors = {
        "<30": "#FF5733",
        "30-50": "#33FF57",
        "50-100": "#3357FF",
        ">100": "#FFC300"
    };
    return colors[group] || "#000000";
}

fetchData();