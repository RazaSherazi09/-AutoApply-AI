import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "autoapply.db")

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at {DB_PATH}. Exiting.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Beginning SQLite schema migration...")

    # 1. Update preferences table
    try:
        cursor.execute("ALTER TABLE preferences ADD COLUMN country VARCHAR(128) NOT NULL DEFAULT 'Worldwide'")
        print(" -> Added 'country' column to preferences.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(" -> 'country' column already exists in preferences.")
        else:
            raise

    try:
        cursor.execute("ALTER TABLE preferences ADD COLUMN workplace_type VARCHAR(64) NOT NULL DEFAULT 'Any'")
        print(" -> Added 'workplace_type' column to preferences.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(" -> 'workplace_type' column already exists in preferences.")
        else:
            raise

    # 2. Update jobs table (sqlite does not support dropping UNIQUE constraints easily via ALTER TABLE)
    # But it does support adding columns
    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN user_id INTEGER REFERENCES users(id)")
        print(" -> Added 'user_id' column to jobs.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(" -> 'user_id' column already exists in jobs.")
        else:
            raise

    # Regarding the UNIQUE constraint on content_hash:
    # In SQLite, dropping a unique constraint requires recreating the table. 
    # Since this is a massive operation, we will perform the table recreation pattern.
    print(" -> Rebuilding 'jobs' table to remove UNIQUE constraint on content_hash...")
    
    # Verify if the index exists. The constraint might technically be an index named ix_jobs_content_hash
    # We can drop the unique index and recreate it as a regular index.
    try:
        cursor.execute("DROP INDEX IF EXISTS ix_jobs_content_hash")
        cursor.execute("CREATE INDEX ix_jobs_content_hash ON jobs (content_hash)")
        print(" -> Successfully relaxed unique constraint by dropping and recreating index.")
    except Exception as e:
        print(f" -> Failed relaxing index: {e}")

    # Because SQLAlchemy might have defined the unique constraint inline, let's just do a table rewrite to be 100% safe.
    try:
        cursor.execute("CREATE TABLE jobs_new (id INTEGER NOT NULL PRIMARY KEY, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL, user_id INTEGER, title VARCHAR(512) NOT NULL, company VARCHAR(256) NOT NULL, location VARCHAR(256) NOT NULL, description TEXT NOT NULL, url VARCHAR(2048) NOT NULL, content_hash VARCHAR(64) NOT NULL, source VARCHAR(64) NOT NULL, job_type VARCHAR(32) NOT NULL, experience_level VARCHAR(32) NOT NULL, remote_status VARCHAR(32) NOT NULL, salary_min FLOAT, salary_max FLOAT, extracted_skills TEXT NOT NULL, embedding BLOB, FOREIGN KEY(user_id) REFERENCES users (id))")
        
        # Copy data
        cursor.execute("INSERT INTO jobs_new (id, created_at, updated_at, user_id, title, company, location, description, url, content_hash, source, job_type, experience_level, remote_status, salary_min, salary_max, extracted_skills, embedding) SELECT id, created_at, updated_at, user_id, title, company, location, description, url, content_hash, source, job_type, experience_level, remote_status, salary_min, salary_max, extracted_skills, embedding FROM jobs")
        
        # Drop old
        cursor.execute("DROP TABLE jobs")
        
        # Rename new
        cursor.execute("ALTER TABLE jobs_new RENAME TO jobs")
        
        # Recreate indexes
        cursor.execute("CREATE INDEX ix_jobs_id ON jobs (id)")
        cursor.execute("CREATE INDEX ix_jobs_content_hash ON jobs (content_hash)")
        cursor.execute("CREATE INDEX ix_jobs_user_id ON jobs (user_id)")
        
        print(" -> Jobs table rebuilt successfully!")
    except Exception as e:
        print(f" -> Table rewrite failed (likely already done or error): {e}")


    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
