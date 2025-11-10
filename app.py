from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'heart_locations.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        conn = get_db_connection()
        # MODIFIED: Added age_range column
        conn.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                age_range TEXT 
            );
        ''')
        conn.commit()
        conn.close()

if not os.path.exists(DATABASE):
    print("Database file not found. Initializing database...")
    init_db()

# --- API Endpoints ---

@app.route('/api/hearts', methods=['GET'])
def get_hearts():
    """Retrieves all heart locations and age ranges."""
    conn = get_db_connection()
    # MODIFIED: Selecting age_range as well
    hearts = conn.execute('SELECT latitude, longitude, age_range FROM locations').fetchall()
    conn.close()
    
    # MODIFIED: Including age_range in the dictionary
    hearts_list = [{'lat': row['latitude'], 'lng': row['longitude'], 'age': row['age_range']} for row in hearts]
    
    return jsonify(hearts_list)

@app.route('/api/hearts', methods=['POST'])
def add_heart():
    """Receives location and age range and saves it to the database."""
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    age_range = data.get('age_range') # MODIFIED: New field

    if latitude is None or longitude is None:
        return jsonify({"error": "Missing latitude or longitude"}), 400

    try:
        conn = get_db_connection()
        # MODIFIED: Added age_range to INSERT statement
        conn.execute('INSERT INTO locations (latitude, longitude, age_range) VALUES (?, ?, ?)',
                     (latitude, longitude, age_range))
        conn.commit()
        conn.close()
        return jsonify({"message": "Heart location added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Run the App and CORS for local testing ---

if __name__ == '__main__':
    @app.after_request
    def add_cors_headers(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST')
        return response

    app.run(debug=True)