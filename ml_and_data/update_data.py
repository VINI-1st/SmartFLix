import pyodbc
import requests
import time
import os
from dotenv import load_dotenv

# Load biến môi trường (nếu ông dùng file .env)
load_dotenv()

# Cấu hình Database - Dùng y hệt như trong main.py của ông
def get_db_connection():
    # Sửa chuỗi kết nối này cho khớp với file main.py của ông
    # Ví dụ:
    conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=VINI\\CLCCSDLPTNHOM3;DATABASE=SmartFlix;Trusted_Connection=yes;"
    return pyodbc.connect(conn_str)

TMDB_API_KEY = "145a8c38c7b2182c288c6fde2be10905"

def update_all_ratings():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("🚀 Đang kết nối database... bắt đầu quét phim...")
    cursor.execute("SELECT MovieID, Title FROM Movies")
    movies = cursor.fetchall()
    
    count = 0
    for movie in movies:
        movie_id = movie.MovieID
        title = movie.Title
        
        # Gọi API TMDB
        url = f"https://api.themoviedb.org/3/movie/{movie_id}/release_dates?api_key={TMDB_API_KEY}"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                cert = None
                for item in data.get('results', []):
                    if item.get('iso_3166_1') == 'US':
                        for d in item.get('release_dates', []):
                            if d.get('certification'):
                                cert = d.get('certification')
                                break
                
                # Ánh xạ chuẩn VN
                vn_rating = "T16"
                if cert:
                    c = cert.upper()
                    if c in ['G', 'PG']: vn_rating = "P"
                    elif c in ['PG-13']: vn_rating = "T13"
                    elif c in ['R', 'NC-17']: vn_rating = "T18"
                
                cursor.execute("UPDATE Movies SET AgeRating = ? WHERE MovieID = ?", (vn_rating, movie_id))
                conn.commit()
                print(f"✅ Đã cập nhật: {title} --> {vn_rating}")
                count += 1
                time.sleep(0.1) # Tránh bị chặn
        except Exception as e:
            print(f"❌ Lỗi phim {title}: {e}")
            
    conn.close()
    print(f"\n🎉 Xong! Đã cập nhật {count} phim.")

if __name__ == "__main__":
    update_all_ratings()