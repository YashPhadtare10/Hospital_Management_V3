import sqlite3
import os
import logging
from database import get_db_path, get_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Migrate the database to add hospital_id to prescriptions table."""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        logger.info("Database does not exist. No migration needed.")
        return
    
    logger.info(f"Starting database migration at: {db_path}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if hospital_id column exists in prescriptions table
        cursor.execute("PRAGMA table_info(prescriptions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'hospital_id' not in columns:
            logger.info("Adding hospital_id column to prescriptions table")
            
            # Create a temporary table with the new schema
            cursor.execute('''
                CREATE TABLE prescriptions_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    appointment_id INTEGER NOT NULL UNIQUE,
                    diagnosis TEXT NOT NULL,
                    medicines TEXT NOT NULL,
                    instructions TEXT,
                    hospital_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (appointment_id) REFERENCES appointments(id),
                    FOREIGN KEY (hospital_id) REFERENCES staff(id)
                )
            ''')
            
            # Copy data from the old table to the new one
            cursor.execute('''
                INSERT INTO prescriptions_new (id, appointment_id, diagnosis, medicines, instructions, created_at)
                SELECT id, appointment_id, diagnosis, medicines, instructions, created_at
                FROM prescriptions
            ''')
            
            # Update hospital_id based on the appointment
            cursor.execute('''
                UPDATE prescriptions_new
                SET hospital_id = (
                    SELECT hospital_id
                    FROM appointments
                    WHERE appointments.id = prescriptions_new.appointment_id
                )
            ''')
            
            # Drop the old table
            cursor.execute('DROP TABLE prescriptions')
            
            # Rename the new table to the original name
            cursor.execute('ALTER TABLE prescriptions_new RENAME TO prescriptions')
            
            conn.commit()
            logger.info("Migration completed successfully")
        else:
            logger.info("hospital_id column already exists in prescriptions table")
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Migration error: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database() 