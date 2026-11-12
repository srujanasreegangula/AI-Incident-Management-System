
import sqlite3

def create_database():
    connection = sqlite3.connect("incidents.db")
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'Open'
        )
    """)

    # Add priority column to existing database
    cursor.execute("PRAGMA table_info(incidents)")
    columns = [column[1] for column in cursor.fetchall()]

    if "priority" not in columns:
        cursor.execute("""
            ALTER TABLE incidents
            ADD COLUMN priority TEXT DEFAULT 'Medium'
        """)

    connection.commit()
    connection.close()

    print("Database created successfully!")

if __name__ == "__main__":
    create_database()
