from flask import Flask, request, jsonify, send_from_directory
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

app = Flask(__name__)

# --- Database Connection Setup (PostgreSQL for Render) ---
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://user:password@localhost:5432/chd_map_db'
)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Database Schema Functions (MODIFIED: Added user_id column) ---

def init_db():
    """Initializes the database schema if the 'locations' table doesn't exist."""
    print("Attempting to initialize database schema...")
    try:
        with engine.connect() as connection:
            # MODIFIED: Added user_id column (TEXT)
            connection.execute(text('''
                CREATE TABLE IF NOT EXISTS locations (
                    id SERIAL PRIMARY KEY,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    age_range TEXT,
                    user_id TEXT NOT NULL
                );
            '''))
            connection.commit()
        print("Database schema successfully initialized.")
    except Exception as e:
        print(f"ERROR: Database initialization failed. Check your connection settings. Error: {e}")

# This call will run, and if your table already exists, it will be skipped.
# We will manually reset the DB on Render to apply the new column structure.
init_db()

# --- Web Service Routes ---
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)


# --- API Endpoints (MODIFIED: Handles user_id) ---

@app.route('/api/hearts', methods=['GET'])
def get_hearts():
    """Retrieves all data, including the user_id for identification."""
    try:
        with SessionLocal() as session:
            # MODIFIED: SELECTING user_id and id
            result = session.execute(text('SELECT id, latitude, longitude, age_range, user_id FROM locations')).fetchall()

            hearts_list = []
            for row in result:
                hearts_list.append({
                    'id': row[0],
                    'lat': row[1],
                    'lng': row[2],
                    'age': row[3],
                    'user_id': row[4] # Send user_id back to client
                })
            return jsonify(hearts_list)
    except Exception as e:
        print(f"Error fetching hearts: {e}")
        return jsonify({"error": "Could not connect to database"}), 500

@app.route('/api/hearts', methods=['POST'])
def add_heart():
    """Receives location, age range, and user ID and saves it."""
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    age_range = data.get('age_range')
    user_id = data.get('user_id') # NEW FIELD

    if latitude is None or longitude is None or user_id is None:
        return jsonify({"error": "Missing required data"}), 400

    try:
        with SessionLocal() as session:
            # MODIFIED: Added user_id to INSERT statement
            session.execute(text('''
                INSERT INTO locations (latitude, longitude, age_range, user_id) 
                VALUES (:lat, :lng, :age, :uid)
            '''), {
                'lat': latitude,
                'lng': longitude,
                'age': age_range,
                'uid': user_id
            })
            session.commit()
            return jsonify({"message": "Heart location added successfully"}), 201
    except Exception as e:
        print(f"Error adding heart: {e}")
        return jsonify({"error": "Could not save location to database"}), 500

# --- NEW DELETE API Endpoint (Will be fully implemented next step) ---
# We will add the secure DELETE route in the next step!


# --- Run the App and CORS for local testing ---
if __name__ == '__main__':
    @app.after_request
    def add_cors_headers(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST')
        return response

    app.run(debug=True)