import sqlite3


def create_database():
    connection = sqlite3.connect("interview.db")
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            score INTEGER,
            total INTEGER,
            percentage REAL
        )
    """)

    connection.commit()
    connection.close()
    print("Database created successfully.")


if __name__ == "__main__":
    create_database()