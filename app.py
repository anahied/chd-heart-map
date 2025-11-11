from flask import Flask, request, jsonify, send_from_directory
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
            # PostgreSQL structure for the locations table, including user_id
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

# Call init_db immediately to set up the structure
init_db()

# --- Web Service Routes ---

@app.route('/')
def serve_index():
    """Serves the index.html file when the user visits the root URL (/)."""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serves any other file (like map-logic.js) from the root directory."""
    return send_from_directory('.', filename)


# --- API Endpoints ---

@app.route('/api/hearts', methods=['GET'])
def get_hearts():
    """Retrieves all heart locations and age ranges, including ID and user_id."""
    try:
        with SessionLocal() as session:
            # Selecting all fields needed for front-end logic (id and user_id are crucial)
            result = session.execute(text('SELECT id, latitude, longitude, age_range, user_id FROM locations')).fetchall()

            hearts_list = []
            for row in result:
                hearts_list.append({
                    'id': row[0],
                    'lat': row[1],
                    'lng': row[2],
                    'age': row[3],
                    'user_id': row[4]
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
    user_id = data.get('user_id')

    if latitude is None or longitude is None or user_id is None:
        return jsonify({"error": "Missing required data"}), 400

    try:
        with SessionLocal() as session:
            # Inserts the new data point
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

@app.route('/api/hearts/<int:heart_id>', methods=['DELETE'])
def delete_heart(heart_id):
    """Deletes a heart if the submitted user_id matches the owner's user_id."""
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"error": "User authentication required"}), 401
    
    try:
        with SessionLocal() as session:
            # 1. Verify ownership by selecting the user_id for the given heart_id
            result = session.execute(text('SELECT user_id FROM locations WHERE id = :id'), {'id': heart_id}).fetchone()

            if not result:
                return jsonify({"error": "Heart not found."}), 404

            db_user_id = result[0]
            
            # 2. Check if the submitted user_id matches the database owner ID
            if db_user_id != user_id:
                return jsonify({"error": "Unauthorized: You do not own this heart."}), 403

            # 3. If authorized, execute deletion
            session.execute(text('DELETE FROM locations WHERE id = :id AND user_id = :uid'), {
                'id': heart_id, 
                'uid': user_id
            })
            session.commit()
            return jsonify({"message": f"Heart ID {heart_id} successfully removed."}), 200

    except Exception as e:
        print(f"Error deleting heart: {e}")
        return jsonify({"error": "Database error during deletion."}), 500

# --- Run the App and CORS for local testing ---

if __name__ == '__main__':
    @app.after_request
    def add_cors_headers(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,DELETE')
        return response

    app.run(debug=True)