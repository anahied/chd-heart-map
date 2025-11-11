// --- Configuration ---
const API_URL = 'https://chd-heart-map-service.onrender.com/api/hearts'; // **CRUCIAL: Replace with your actual Render URL**

// --- User ID Management (NEW CODE BLOCK) ---
function generateUUID() {
    // Generates a simple but unique ID (UUID format)
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function getUserId() {
    let userId = localStorage.getItem('chd_map_user_id');
    if (!userId) {
        userId = generateUUID();
        localStorage.setItem('chd_map_user_id', userId);
        console.log("New anonymous user ID generated:", userId);
    }
    return userId;
}

const CURRENT_USER_ID = getUserId();
console.log("Using User ID:", CURRENT_USER_ID);
// ---------------------------------------------


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

// 4. Handle user clicking the map (MODIFIED: Sends user ID)
map.on('click', function(e) {
    // Get location coordinates
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;

    // Get the selected age range from the dropdown
    const ageSelect = document.getElementById('age-select');
    const ageRange = ageSelect.value;
    
    let popupText = `Location Shared!`;
    if (ageRange) {
        popupText += `<br>Age Range: <b>${ageRange}</b>`;
    }

    // A. Place a marker immediately
    L.marker([lat, lng], {icon: HeartIcon}).addTo(map)
        .bindPopup(popupText + "<br>This is yours!") // Temporary feedback
        .openPopup();

    // B. Send data to the Flask server
    fetch(API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        // MODIFIED: Added user_id to the body
        body: JSON.stringify({ 
            latitude: lat, 
            longitude: lng,
            age_range: ageRange,
            user_id: CURRENT_USER_ID // Send the unique ID
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

// 5. LOAD ALL EXISTING HEARTS from the server (MODIFIED: Checks for current user's hearts)
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
                const age = location.age || "Not Specified"; 
                const heartId = location.id; // Get the heart's unique DB ID
                const heartUserId = location.user_id; // Get the ID of the user who placed it

                if (!isNaN(markerLat) && !isNaN(markerLng)) {
                    // Start popup content
                    let popupContent = `Location Shared!<br>Age Range: <b>${age}</b>`;
                    
                    // NEW LOGIC: Check if the heart belongs to the current user
                    if (heartUserId === CURRENT_USER_ID) {
                        popupContent += `<br><button class="delete-btn" data-id="${heartId}">Remove My Heart</button>`;
                    }
                    
                    L.marker([markerLat, markerLng], {icon: HeartIcon}).addTo(map)
                        .bindPopup(popupContent);
                }
            });
            console.log(`Successfully loaded ${data.length} existing heart locations.`);
            // ADD EVENT LISTENER FOR DELETE BUTTONS
            addDeleteEventListeners();
        })
        .catch(error => {
            console.error('Could not load existing heart locations:', error);
        });
}

// 6. Delete Event Listener (NEW FUNCTION)
function addDeleteEventListeners() {
    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', function() {
            const heartId = this.getAttribute('data-id');
            if (confirm(`Are you sure you want to remove heart ID ${heartId}?`)) {
                // We'll implement the actual DELETE fetch request later!
                console.log(`Ready to send DELETE request for heart ID: ${heartId}`);
                // TODO: Implement the actual deleteHeart function here
            }
        });
    });
}

loadExistingHearts();