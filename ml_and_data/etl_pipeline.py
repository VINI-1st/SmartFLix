import os
import requests
import pyodbc
from dotenv import load_dotenv

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG
# ==========================================
load_dotenv()
SERVER_NAME = os.getenv("DB_SERVER")
DATABASE_NAME = os.getenv("DB_NAME")
# Tự động lấy API Key từ .env, nếu không có thì dùng key mặc định của ông
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "145a8c38c7b2182c288c6fde2be10905")

conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER_NAME};DATABASE={DATABASE_NAME};Trusted_Connection=yes;"

def get_db_connection():
    return pyodbc.connect(conn_str)

# ==========================================
# 2. HÀM CẬP NHẬT THỂ LOẠI (GENRES)
# ==========================================
def sync_genres(cursor):
    print("📥 Đang lấy danh sách Thể loại từ TMDB...")
    url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={TMDB_API_KEY}&language=vi-VN"
    res = requests.get(url).json()
    
    if 'genres' in res:
        for genre in res['genres']:
            # Kiểm tra xem Thể loại đã có chưa để tránh trùng lặp
            cursor.execute("SELECT 1 FROM Genres WHERE GenreID = ?", genre['id'])
            if not cursor.fetchone():
                cursor.execute("INSERT INTO Genres (GenreID, GenreName) VALUES (?, ?)", (genre['id'], genre['name']))
        print("✅ Đã cập nhật xong bảng Genres!")

# ==========================================
# 3. HÀM CÀO PHIM VÀ PHÂN LOẠI (MOVIES & MOVIE_GENRE)
# ==========================================
# ... (Phần đầu giữ nguyên) ...

def sync_movies(cursor, conn, total_pages=15):
    print(f"🎬 Bắt đầu cào {total_pages} trang Phim...")
    new_movies_count = 0  # Biến đếm số phim mới lưu thành công
    
    for page in range(1, total_pages + 1):
        url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&language=vi-VN&page={page}"
        res = requests.get(url).json()
        
        if 'results' not in res: continue
            
        for movie in res['results']:
            movie_id = movie.get('id')
            # ... (Các bước lấy thông tin movie_id, title... giữ nguyên) ...
            title = movie.get('title')
            original_title = movie.get('original_title')
            overview = movie.get('overview', '')
            release_date = movie.get('release_date', '')
            release_year = int(release_date.split('-')[0]) if release_date else None
            poster_path = movie.get('poster_path')
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            genre_ids = movie.get('genre_ids', [])

            cursor.execute("SELECT 1 FROM Movies WHERE MovieID = ?", movie_id)
            if not cursor.fetchone():
                try:
                    cursor.execute("""
                        INSERT INTO Movies (MovieID, Title, OriginalTitle, Overview, ReleaseYear, PosterURL)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (movie_id, title, original_title, overview, release_year, poster_url))
                    
                    for genre_id in genre_ids:
                        cursor.execute("SELECT 1 FROM Genres WHERE GenreID = ?", genre_id)
                        if cursor.fetchone():
                            cursor.execute("INSERT INTO Movie_Genre (MovieID, GenreID) VALUES (?, ?)", (movie_id, genre_id))
                    
                    conn.commit()
                    new_movies_count += 1 # Tăng biến đếm
                    print(f"✅ Đã lưu: {title}")
                except Exception as e:
                    conn.rollback()
    
    return new_movies_count # Trả về tổng số phim mới

if __name__ == "__main__":
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sync_genres(cursor)
        conn.commit()
        
        # Nhận kết quả từ hàm sync_movies
        total_saved = sync_movies(cursor, conn, total_pages=50)
        
        print("\n" + "="*50)
        print(f"🎉 HOÀN THÀNH QUY TRÌNH ETL!")
        print(f"🚀 Tổng số phim mới đã nạp vào Database: {total_saved}")
        print("="*50)
        
    except Exception as e:
        print(f"💥 Lỗi: {e}")
    finally:
        if 'conn' in locals(): conn.close()