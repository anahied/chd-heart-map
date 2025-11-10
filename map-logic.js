const API_URL = 'http://127.0.0.1:5000/api/hearts';

// 1. Initialize the map
const map = L.map('map').setView([39.8283, -98.5795], 4); 

// 2. Add the base tile layer
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// 3. Define the custom heart icon
const HeartIcon = L.divIcon({
    className: 'heart-icon',
    html: '❤️', 
    iconSize: [28, 28],
    iconAnchor: [14, 28] 
});

// 4. Handle user clicking the map (MODIFIED)
map.on('click', function(e) {
    // Get location coordinates
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;

    // MODIFIED: Get the selected age range from the dropdown
    const ageSelect = document.getElementById('age-select');
    const ageRange = ageSelect.value;
    
    let popupText = `Location Shared!`;
    if (ageRange) {
        popupText += `<br>Age Range: <b>${ageRange}</b>`;
    }

    // A. Place a marker immediately
    L.marker([lat, lng], {icon: HeartIcon}).addTo(map)
        .bindPopup(popupText)
        .openPopup();

    // B. Send data to the Flask server
    fetch(API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        // MODIFIED: Added age_range to the body
        body: JSON.stringify({ 
            latitude: lat, 
            longitude: lng,
            age_range: ageRange // Send the new data field
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Server response:", data.message);
    })
    .catch(error => {
        console.error('Error saving location. Is the server running?', error);
    });
});

// 5. LOAD ALL EXISTING HEARTS from the server (MODIFIED)
function loadExistingHearts() {
    fetch(API_URL)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            data.forEach(location => {
                const markerLat = parseFloat(location.lat);
                const markerLng = parseFloat(location.lng);
                const age = location.age || "Not Specified"; // MODIFIED: Get age range

                if (!isNaN(markerLat) && !isNaN(markerLng)) {
                    L.marker([markerLat, markerLng], {icon: HeartIcon}).addTo(map)
                        // MODIFIED: Added age range to the marker popup
                        .bindPopup(`Location Shared!<br>Age Range: <b>${age}</b>`);
                }
            });
            console.log(`Successfully loaded ${data.length} existing heart locations.`);
        })
        .catch(error => {
            console.error('Could not load existing heart locations:', error);
        });
}

loadExistingHearts();