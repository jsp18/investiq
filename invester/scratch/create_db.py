import pymysql
from config import Config

def create_db():
    print(f"Connecting to MySQL at {Config.MYSQL_HOST} to create database '{Config.MYSQL_DB}'...")
    try:
        # Connect without database name
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB}")
        print(f"Database '{Config.MYSQL_DB}' created or already exists.")
        conn.close()
    except Exception as e:
        print(f"Failed to create database: {e}")

if __name__ == "__main__":
    create_db()
