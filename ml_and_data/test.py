import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

def test():
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    # Thử kết nối trực tiếp với Driver 17
    conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;"
    
    print(f"Đang thử kết nối tới: {server}...")
    try:
        conn = pyodbc.connect(conn_str, timeout=5)
        print("✅ Kết nối thành công rực rỡ!")
        conn.close()
    except Exception as e:
        print("❌ Vẫn lỗi rồi. Chi tiết:")
        print(e)

if __name__ == "__main__":
    test()