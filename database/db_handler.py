import mysql.connector
import os
from dotenv import load_dotenv

# .env ফাইল থেকে ডেটা লোড করা
load_dotenv()

def get_db_connection():
    """
    ডেটাবেজের সাথে কানেকশন তৈরি করে এবং কানেকশন অবজেক্ট রিটার্ন করে।
    """
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        if connection.is_connected():
            return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

# কানেকশন টেস্ট করার জন্য ছোট ফাংশন
if __name__ == "__main__":
    conn = get_db_connection()
    if conn:
        print("🚀 Successfully connected to Coaching360 database!")
        conn.close()