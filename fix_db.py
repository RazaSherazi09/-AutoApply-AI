import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "autoapply.db")

def fix_jobs_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Fixing jobs table default timestamps...")

    try:
        cursor.execute("CREATE TABLE jobs_fixed (id INTEGER NOT NULL PRIMARY KEY, created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, user_id INTEGER REFERENCES users(id), title VARCHAR(512) NOT NULL, company VARCHAR(256) NOT NULL, location VARCHAR(256) NOT NULL, description TEXT NOT NULL, url VARCHAR(2048) NOT NULL, content_hash VARCHAR(64) NOT NULL, source VARCHAR(64) NOT NULL, job_type VARCHAR(32) NOT NULL, experience_level VARCHAR(32) NOT NULL, remote_status VARCHAR(32) NOT NULL, salary_min FLOAT, salary_max FLOAT, extracted_skills TEXT NOT NULL, embedding BLOB)")
        
        # Copy data
        cursor.execute("INSERT INTO jobs_fixed SELECT * FROM jobs")
        
        # Drop old
        cursor.execute("DROP TABLE jobs")
        
        # Rename new
        cursor.execute("ALTER TABLE jobs_fixed RENAME TO jobs")
        
        # Recreate indexes
        cursor.execute("CREATE INDEX ix_jobs_id ON jobs (id)")
        cursor.execute("CREATE INDEX ix_jobs_content_hash ON jobs (content_hash)")
        cursor.execute("CREATE INDEX ix_jobs_user_id ON jobs (user_id)")
        
        print(" -> Jobs table fixed successfully!")
        conn.commit()
    except Exception as e:
        print(f" -> Fix failed: {e}")
        conn.rollback()

    conn.close()

if __name__ == "__main__":
    fix_jobs_table()
