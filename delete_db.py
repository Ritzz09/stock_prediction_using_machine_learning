import sqlite3
from datetime import datetime, timedelta

# Function to get database connection
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    return conn

# Function to delete all data from the users table
def delete_all_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete all rows from the users table
    cursor.execute('DELETE FROM users')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    print("All data has been deleted from the users table.")

# Function to drop and reset the users table completely
def reset_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Drop the users table completely
    cursor.execute('DROP TABLE IF EXISTS users')

    # Recreate the users table with the updated schema
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        mobile TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_login DATETIME
    )
    ''')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    print("Database has been reset and the users table has been recreated.")

# Function to delete inactive users (users who haven't logged in for more than 1 year)
def delete_inactive_users():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get the current date minus 1 year
    one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S')


# Main entry point to run the functions
if __name__ == '__main__':
    # Uncomment the function you want to execute
    
    # Reset the database (drops and recreates the table)
    # reset_database()

    # Or, delete all data but keep the table structure
    # delete_all_data()

    # Or, delete inactive users who haven't logged in for a year
    delete_inactive_users()
