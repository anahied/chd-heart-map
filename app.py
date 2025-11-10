from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import urllib.parse

app = Flask(__name__)

# --- Database Connection Setup ---

# 1. Use the DATABASE_URL environment variable provided by the hosting service.
#    If running locally, use a dummy URL for now (we'll connect a real one later).
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    # Dummy URL for local testing, will not connect until you set up PostgreSQL locally
    'postgresql://user:password@localhost:5432/chd_map_db'
)

# Render uses 'postgres://' which must be converted to 'postgresql://' for SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Database Schema Functions ---

def init_db():
    """Initializes the database schema if the 'locations' table doesn't exist."""
    print("Attempting to initialize database schema...")
    try:
        with engine.connect() as connection:
            # PostgreSQL uses TEXT for string fields, and SERIAL for auto-incrementing IDs
            connection.execute(text('''
                CREATE TABLE IF NOT EXISTS locations (
                    id SERIAL PRIMARY KEY,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    age_range TEXT
                );
            '''))
            connection.commit()
        print("Database schema successfully initialized.")
    except Exception as e:
        print(f"ERROR: Database initialization failed. Check your connection settings. Error: {e}")

# Call init_db immediately to set up the structure
init_db()

# --- API Endpoints ---

@app.route('/api/hearts', methods=['GET'])
def get_hearts():
    """Retrieves all heart locations and age ranges from PostgreSQL."""
    try:
        with SessionLocal() as session:
            # Selects all data from the locations table
            result = session.execute(text('SELECT latitude, longitude, age_range FROM locations')).fetchall()

            hearts_list = []
            for row in result:
                hearts_list.append({
                    'lat': row[0],
                    'lng': row[1],
                    'age': row[2]
                })
            return jsonify(hearts_list)
    except Exception as e:
        print(f"Error fetching hearts: {e}")
        return jsonify({"error": "Could not connect to database"}), 500

@app.route('/api/hearts', methods=['POST'])
def add_heart():
    """Receives location and age range and saves it to PostgreSQL."""
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    age_range = data.get('age_range')

    if latitude is None or longitude is None:
        return jsonify({"error": "Missing latitude or longitude"}), 400

    try:
        with SessionLocal() as session:
            # Inserts the new data point
            session.execute(text('''
                INSERT INTO locations (latitude, longitude, age_range) 
                VALUES (:lat, :lng, :age)
            '''), {
                'lat': latitude,
                'lng': longitude,
                'age': age_range
            })
            session.commit()
            return jsonify({"message": "Heart location added successfully"}), 201
    except Exception as e:
        print(f"Error adding heart: {e}")
        return jsonify({"error": "Could not save location to database"}), 500

# --- Run the App and CORS for local testing ---

if __name__ == '__main__':
    @app.after_request
    def add_cors_headers(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST')
        return response

    # Use Gunicorn locally for better testing parity
    # Note: Flask's built-in server is fine for local testing, but using Gunicorn (if installed)
    # is closer to the production environment.
    app.run(debug=True)