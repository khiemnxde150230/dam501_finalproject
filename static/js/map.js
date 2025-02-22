// Initialize Map
const map = L.map('map').setView([16.047079, 108.206230], 12); // Centered on Da Nang City

// Add OpenStreetMap Tile Layer
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

async function fetchData() {
    const response = await fetch("/api/apartment-map", {
        headers: { "Accept": "application/json" }  // ✅ Ensure JSON response
    });
    const data = await response.json();
    console.log(data)
    // Filter data for Da Nang city
    // Da Nang coordinates approximately: 15.9750° N to 16.1250° N, 108.1500° E to 108.2500° E
    const daNangData = data.filter(item => 
        item.latitude >= 15.9750 && item.latitude <= 16.1250 &&
        item.longitude >= 108.1500 && item.longitude <= 108.2500
    );

    // Add Markers to Map
    daNangData.forEach(location => {
        const marker = L.marker([location.latitude, location.longitude]).addTo(map);
        marker.bindPopup(`<b>Area:</b> ${location.area} m²<br><b>Price:</b> ${location.price.toLocaleString()} VND`);
    });
}

fetchData()