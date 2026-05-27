import pyodbc
import requests
import time
import os
from dotenv import load_dotenv

# Load biến môi trường
load_dotenv()

def get_db_connection():
    # Giữ nguyên chuỗi kết nối chuẩn của ông
    conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=VINI\\CLCCSDLPTNHOM3;DATABASE=SmartFlix;Trusted_Connection=yes;"
    return pyodbc.connect(conn_str)

TMDB_API_KEY = "145a8c38c7b2182c288c6fde2be10905"

def update_all_languages():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("🚀 Đang kết nối database... bắt đầu quét ngôn ngữ phim...")
    
    # 🛑 SỬA LỆNH SQL: Gọi thêm cột IsSeries ra để kiểm tra
    cursor.execute("SELECT MovieID, Title, IsSeries FROM Movies WHERE OriginalLanguage IS NULL")
    movies = cursor.fetchall()
    
    if not movies:
        print("✅ Tất cả các phim đều đã có ngôn ngữ. Không cần cập nhật thêm!")
        conn.close()
        return

    count = 0
    for movie in movies:
        movie_id = movie.MovieID
        title = movie.Title
        is_series = movie.IsSeries # Lấy cờ đánh dấu phim bộ
        
        # 🛑 RẼ NHÁNH ĐƯỜNG DẪN API
        if is_series == 1:
            # Nếu là phim bộ thì chui vào cổng /tv/
            url = f"https://api.themoviedb.org/3/tv/{movie_id}?api_key={TMDB_API_KEY}"
        else:
            # Nếu là phim lẻ thì chui vào cổng /movie/
            url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"

        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                lang = data.get('original_language', 'en') 
                
                cursor.execute("UPDATE Movies SET OriginalLanguage = ? WHERE MovieID = ?", (lang, movie_id))
                conn.commit()
                print(f"✅ Đã cập nhật: {title} --> Ngôn ngữ: {lang.upper()}")
                count += 1
                
                time.sleep(0.1) 
            else:
                print(f"⚠️ Không tìm thấy phim {title} trên TMDB (Mã lỗi: {res.status_code}) - URL: {url}")
        except Exception as e:
            print(f"❌ Lỗi phim {title}: {e}")
            
    conn.close()
    print(f"\n🎉 Xong! Đã cập nhật ngôn ngữ Real Data cho {count} phim.")

if __name__ == "__main__":
    update_all_languages()