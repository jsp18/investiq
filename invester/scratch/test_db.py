import pymysql
from config import Config

def test_conn():
    print(f"Testing connection to {Config.MYSQL_HOST} as {Config.MYSQL_USER} (no DB specified)...")
    try:
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD
        )
        print("Login successful!")
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall()]
        print(f"Databases: {databases}")
        if Config.MYSQL_DB in databases:
            print(f"Found {Config.MYSQL_DB}")
        else:
            print(f"CRITICAL: {Config.MYSQL_DB} NOT FOUND. You must create it.")
        conn.close()
    except Exception as e:
        print(f"Login failed: {e}")

if __name__ == "__main__":
    test_conn()
