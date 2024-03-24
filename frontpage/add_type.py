import sqlite3
import sys

# Ensure there's at least one command-line argument (excluding the script name)
if len(sys.argv) < 2:
    print("Usage: python add_type.py 'new type'")
    sys.exit(1)

# The rest of the command-line arguments form the article type name
article_type_name = " ".join(sys.argv[1:])

# Connect to SQLite database in the /instance directory
conn = sqlite3.connect("/instance/your_database.db")
c = conn.cursor()

# Create the 'article_types' table if it doesn't exist
c.execute(
    """CREATE TABLE IF NOT EXISTS article_types (
                id INTEGER PRIMARY KEY,
                type_name TEXT NOT NULL UNIQUE
             )"""
)

# Try to insert the new article type, handle potential errors (e.g., duplicate types)
try:
    c.execute("INSERT INTO article_types (type_name) VALUES (?)", (article_type_name,))
    conn.commit()
    print(f"Article type '{article_type_name}' has been added successfully.")
except sqlite3.IntegrityError as e:
    print(f"Error: Could not add the article type '{article_type_name}'. It may already exist.")
finally:
    # Close the connection to the database
    conn.close()
