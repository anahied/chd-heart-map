from flask import Flask, request, jsonify, send_from_directory # MODIFIED: Added send_from_directory
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

app = Flask(__name__)

# --- Database Connection Setup (PostgreSQL for Render) ---

# Get the DATABASE_URL environment variable set by Render
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    # Dummy URL for local testing (won't connect without local PostgreSQL setup)
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
            # PostgreSQL structure for the locations table
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
        # In deployment, this is often due to a connection issue
        print(f"ERROR: Database initialization failed. Check your connection settings. Error: {e}")

# Call init_db immediately to set up the structure
init_db()

# --- Web Service Route (The Fix for 'Not Found') ---

@app.route('/')
def serve_index():
    """Serves the index.html file when the user visits the root URL (/)."""
    # This tells Flask to look in the current directory ('.') for 'index.html'
    return send_from_directory('.', 'index.html')


# --- API Endpoints ---

@app.route('/api/hearts', methods=['GET'])
def get_hearts():
    """Retrieves all heart locations and age ranges from PostgreSQL."""
    try:
        with SessionLocal() as session:
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
            # Inserts the new data point using parameterized query
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

    app.run(debug=True)