import pymysql
from config import Config

def test_passwords():
    passwords = [Config.MYSQL_PASSWORD, "", "root", "password", "1234", "123456"]
    for p in passwords:
        print(f"Testing password: '{p}'")
        try:
            conn = pymysql.connect(host='localhost', user='root', password=p)
            print(f"SUCCESS! Password is '{p}'")
            conn.close()
            return p
        except Exception as e:
            print(f"Failed: {e}")
    return None

if __name__ == "__main__":
    test_passwords()
