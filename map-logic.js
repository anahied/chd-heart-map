// --- Configuration ---
// **CRUCIAL: Replace this URL with your actual Public Live URL from Render**
const API_BASE_URL = 'https://chd-heart-map-service.onrender.com/api/hearts'; 

// --- User ID Management ---
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

// 4. Handle user clicking the map
map.on('click', function(e) {
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;
    const ageSelect = document.getElementById('age-select');
    const ageRange = ageSelect.value;
    
    let popupText = `Location Shared!`;
    if (ageRange) {
        popupText += `<br>Age Range: <b>${ageRange}</b>`;
    }

    L.marker([lat, lng], {icon: HeartIcon}).addTo(map)
        .bindPopup(popupText)
        .openPopup();

    // Send data to the Flask server
    fetch(API_BASE_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
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

// 5. LOAD ALL EXISTING HEARTS from the server
function loadExistingHearts() {
    // Clear existing markers before loading (important for reload!)
    map.eachLayer(function(layer) {
        if (layer.options.icon && layer.options.icon.options.className === 'heart-icon') {
            map.removeLayer(layer);
        }
    });

    fetch(API_BASE_URL)
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
                const heartId = location.id; 
                const heartUserId = location.user_id; 

                if (!isNaN(markerLat) && !isNaN(markerLng)) {
                    let popupContent = `Location Shared!<br>Age Range: <b>${age}</b>`;
                    
                    // Logic: Check if the heart belongs to the current user
                    if (heartUserId === CURRENT_USER_ID) {
                        popupContent += `<br><button class="delete-btn" data-id="${heartId}">Remove My Heart</button>`;
                    }
                    
                    L.marker([markerLat, markerLng], {icon: HeartIcon}).addTo(map)
                        .bindPopup(popupContent);
                }
            });
            console.log(`Successfully loaded ${data.length} existing heart locations.`);
            addDeleteEventListeners();
        })
        .catch(error => {
            console.error('Could not load existing heart locations:', error);
        });
}

// 6. Delete Event Listener
function addDeleteEventListeners() {
    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', function() {
            const heartId = this.getAttribute('data-id');
            
            if (confirm(`Are you sure you want to remove heart ID ${heartId}? This cannot be undone.`)) {
                deleteHeart(heartId);
            }
        });
    });
}

// 7. Deletion Fetch Function
function deleteHeart(heartId) {
    const deleteURL = `${API_BASE_URL}/${heartId}`;

    fetch(deleteURL, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        },
        // Send the user ID so the server can verify ownership
        body: JSON.stringify({ 
            user_id: CURRENT_USER_ID
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || "Deletion failed."); });
        }
        return response.json();
    })
    .then(data => {
        alert(data.message);
        // Reload markers without reloading the whole page for a smoother UX
        loadExistingHearts(); 
    })
    .catch(error => {
        console.error('Deletion Error:', error.message);
        alert(`Deletion failed: ${error.message}`);
    });
}

loadExistingHearts();