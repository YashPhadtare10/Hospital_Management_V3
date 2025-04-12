import sqlite3
import os
import logging
from werkzeug.security import generate_password_hash
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_path():
    """Determine the appropriate database path for different environments."""
    # Use a path within the application's directory structure
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if we're running on Render
    if 'RENDER' in os.environ:
        # Use a directory within the application's directory
        db_dir = os.path.join(app_dir, 'data')
        # Ensure the directory exists
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Created database directory: {db_dir}")
        return os.path.join(db_dir, 'hospital.db')
    else:
        # Local development path
        instance_path = os.path.join(app_dir, 'instance')
        if not os.path.exists(instance_path):
            os.makedirs(instance_path, exist_ok=True)
            logger.info(f"Created instance directory: {instance_path}")
        return os.path.join(instance_path, 'hospital.db')

def init_db():
    """Initialize the database with tables and default admin account."""
    db_path = get_db_path()
    
    # Create directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        logger.info(f"Created database directory: {db_dir}")

    logger.info(f"Initializing database at: {db_path}")
    
    # Check if database exists
    db_exists = os.path.exists(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        if not db_exists:
            logger.info("Creating new database with tables")
            # Create tables with improved schema
            cursor.executescript('''
            CREATE TABLE staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                hospital_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                specialization TEXT NOT NULL,
                experience INTEGER,
                consultation_fee REAL,
                contact TEXT,
                bio TEXT,
                image_path TEXT,
                username TEXT UNIQUE,
                password TEXT,
                created_by INTEGER,
                hospital_id INTEGER NOT NULL,
                FOREIGN KEY (created_by) REFERENCES staff(id),
                FOREIGN KEY (hospital_id) REFERENCES staff(id)
            );

            CREATE TABLE patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT,
                contact TEXT,
                address TEXT,
                medical_history TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                hospital_id INTEGER NOT NULL,
                FOREIGN KEY (created_by) REFERENCES staff(id),
                FOREIGN KEY (hospital_id) REFERENCES staff(id)
            );

            CREATE TABLE appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                status TEXT DEFAULT 'Scheduled',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                hospital_id INTEGER NOT NULL,
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (doctor_id) REFERENCES doctors(id),
                FOREIGN KEY (hospital_id) REFERENCES staff(id)
            );

            CREATE TABLE prescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id INTEGER NOT NULL UNIQUE,
                diagnosis TEXT NOT NULL,
                medicines TEXT NOT NULL,
                instructions TEXT,
                hospital_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (appointment_id) REFERENCES appointments(id),
                FOREIGN KEY (hospital_id) REFERENCES staff(id)
            );

            CREATE TABLE doctor_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_id INTEGER NOT NULL,
                day_of_week TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                break_start TEXT,
                break_end TEXT,
                hospital_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doctor_id) REFERENCES doctors(id),
                FOREIGN KEY (hospital_id) REFERENCES staff(id)
            );
            ''')
            
            # Create default admin account
            default_password = generate_password_hash('admin123')
            cursor.execute('''
            INSERT INTO staff (name, email, password, hospital_name)
            VALUES (?, ?, ?, ?)
            ''', ('Admin', 'admin@hospital.com', default_password, 'General Hospital'))
            
            conn.commit()
            logger.info("Database initialized successfully with default admin account")
        else:
            logger.info("Database already exists, skipping initialization")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        conn.close()

def get_db_connection():
    """Create and return a database connection with row factory."""
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            db_path = get_db_path()
            # Ensure the database directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            conn = sqlite3.connect(db_path, timeout=20)  # Increased timeout
            conn.row_factory = sqlite3.Row
            
            # Test the connection
            conn.execute("SELECT 1")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            raise
        except Exception as e:
            logger.error(f"Unexpected error during database connection: {e}")
            raise

def check_database_exists():
    """Check if the database file exists."""
    db_path = get_db_path()
    return os.path.exists(db_path)

if __name__ == '__main__':
    if not check_database_exists():
        print("Initializing database...")
        init_db()
    else:
        print("Database already exists at:", get_db_path())