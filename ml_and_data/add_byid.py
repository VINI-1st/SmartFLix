import pyodbc
import requests

# Cấu hình Database y hệt file cũ
DB_CONFIG = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=VINI\CLCCSDLPTNHOM3;'  
    r'DATABASE=SmartFlix;'
    r'Trusted_Connection=yes;'
)
TMDB_API_KEY = "145a8c38c7b2182c288c6fde2be10905"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def add_movie_by_id(tmdb_id, is_series=False):
    conn = pyodbc.connect(DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # 1. Kiểm tra xem kho đã có chưa
        cursor.execute("SELECT 1 FROM Movies WHERE MovieID = ?", (tmdb_id,))
        if cursor.fetchone():
            print(f"⚠️ Phim có ID {tmdb_id} đã nằm sẵn trong kho rồi!")
            return

        # 2. Gọi API lấy chính xác 1 phim đó
        type_str = "tv" if is_series else "movie"
        url = f"https://api.themoviedb.org/3/{type_str}/{tmdb_id}?api_key={TMDB_API_KEY}&language=vi-VN"
        
        res = requests.get(url, headers=HEADERS)
        if res.status_code != 200:
            print(f"❌ Không tìm thấy ID {tmdb_id} trên TMDB!")
            return
            
        item = res.json()
        
        # 3. Chuẩn hóa dữ liệu
        overview = item.get('overview', '').strip()
        if not overview: overview = "Nội dung tóm tắt đang được cập nhật..."
            
        poster = f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get('poster_path') else ""
        
        if is_series:
            title = item.get('name', '')
            original_title = item.get('original_name', '')
            date_str = item.get('first_air_date', '')
        else:
            title = item.get('title', '')
            original_title = item.get('original_title', '')
            date_str = item.get('release_date', '')
            
        year_str = date_str[:4] if date_str else '2024'
        year = int(year_str) if year_str.isdigit() else 2024

        # 4. Bơm vào SQL Server
        cursor.execute("""
            INSERT INTO Movies (MovieID, Title, OriginalTitle, PosterURL, Overview, ReleaseYear, IsSeries) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (tmdb_id, title, original_title, poster, overview, year, 1 if is_series else 0))
        
        # Ở endpoint chi tiết, thể loại nó nằm trong mảng 'genres' (chứa object) chứ không phải 'genre_ids'
        for g in item.get('genres', []):
            try:
                cursor.execute("INSERT INTO Movie_Genre (MovieID, GenreID) VALUES (?, ?)", (tmdb_id, g['id']))
            except:
                pass
                
        conn.commit()
        print(f"ĐÃ CÀO THÀNH CÔNG: {title} ({original_title})")
        
    except Exception as e:
        print(f"❌ Lỗi SQL: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("BẮT ĐẦU CÀO PHIM BẰNG ID...")
    
    # Kéo siêu phẩm Taxi Driver (ID: 114638, Phim bộ)
    add_movie_by_id(119769, is_series=True)
    
    # Ví dụ ông muốn kéo thêm phim lẻ Joker (ID: 475557) thì gõ thêm dòng này:
    # add_movie_by_id(475557, is_series=False)