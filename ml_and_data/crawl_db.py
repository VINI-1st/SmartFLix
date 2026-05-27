import pyodbc
import requests
import time

# ==========================================
# CẤU HÌNH KẾT NỐI
# ==========================================
DB_CONFIG = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=VINI\CLCCSDLPTNHOM3;'  
    r'DATABASE=SmartFlix;'
    r'Trusted_Connection=yes;'
)

TMDB_API_KEY = "145a8c38c7b2182c288c6fde2be10905"
HEADERS = {"User-Agent": "Mozilla/5.0"} 

def get_db_connection():
    return pyodbc.connect(DB_CONFIG)

# ==========================================
# HÀM CÀO PHIM LẺ (TIẾNG ANH)
# ==========================================
def crawl_movies(pages=30):
    print(f"\n🎬 [MOVIES] Đang cào dữ liệu tiếng Anh...")
    conn = get_db_connection()
    cursor = conn.cursor()
    total_added = 0
    
    for page in range(1, pages + 1):
        # 🛑 Đã đổi ngôn ngữ sang en-US
        url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&language=en-US&page={page}"
        
        try:
            res = requests.get(url, headers=HEADERS).json()
            page_added = 0
            
            for item in res.get('results', []):
                movie_id = item['id']
                
                # Tóm tắt tiếng Anh
                overview = item.get('overview', '').strip()
                if not overview:
                    overview = "Overview is currently unavailable."
                    
                try:
                    cursor.execute("SELECT 1 FROM Movies WHERE MovieID = ?", (movie_id,))
                    if not cursor.fetchone(): 
                        original_title = item.get('original_title', '')
                        title = item.get('title', '')
                        poster = f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}"
                        
                        release_date = item.get('release_date', '')
                        year_str = release_date[:4] if release_date else '2024'
                        year = int(year_str) if year_str.isdigit() else 2024

                        cursor.execute("""
                            INSERT INTO Movies (MovieID, Title, OriginalTitle, PosterURL, Overview, ReleaseYear, IsSeries) 
                            VALUES (?, ?, ?, ?, ?, ?, 0)
                        """, (movie_id, title, original_title, poster, overview, year))
                        
                        for genre_id in item.get('genre_ids', []):
                            try:
                                cursor.execute("INSERT INTO Movie_Genre (MovieID, GenreID) VALUES (?, ?)", (movie_id, genre_id))
                            except Exception:
                                pass
                        
                        page_added += 1
                        total_added += 1
                        print(f"   [OK] {title}")
                except Exception as e:
                    print(f"   [LỖI SQL] {item.get('title')}: {e}")
            
            conn.commit()
            print(f"✅ Xong trang {page}: Thêm {page_added} phim.")
        except Exception as e:
            print(f"❌ Lỗi gọi API trang {page}: {e}")
        time.sleep(0.5) 
        
    conn.close()
    print(f"✔️ HOÀN TẤT PHIM LẺ! Tổng số: {total_added}")

# ==========================================
# HÀM CÀO PHIM BỘ (TIẾNG ANH + CHẶN THỜI SỰ)
# ==========================================
def crawl_series(pages=30):
    print(f"\n📺 [TV SHOWS] Đang cào dữ liệu tiếng Anh (đã chặn News/Talkshow)...")
    conn = get_db_connection()
    cursor = conn.cursor()
    total_added = 0
    
    for page in range(1, pages + 1):
        # 🛑 Đã đổi sang en-US VÀ thêm without_genres để loại bỏ Thời sự, Talkshow
        url = f"https://api.themoviedb.org/3/tv/popular?api_key={TMDB_API_KEY}&language=en-US&without_genres=10763,10767,10764&page={page}"
        
        try:
            res = requests.get(url, headers=HEADERS).json()
            page_added = 0
            
            for item in res.get('results', []):
                movie_id = item['id']
                
                overview = item.get('overview', '').strip()
                if not overview:
                    overview = "Overview is currently unavailable."

                try:
                    cursor.execute("SELECT 1 FROM Movies WHERE MovieID = ?", (movie_id,))
                    if not cursor.fetchone():
                        original_name = item.get('original_name', '')
                        name = item.get('name', '')
                        poster = f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}"
                        
                        first_air_date = item.get('first_air_date', '')
                        year_str = first_air_date[:4] if first_air_date else '2024'
                        year = int(year_str) if year_str.isdigit() else 2024

                        cursor.execute("""
                            INSERT INTO Movies (MovieID, Title, OriginalTitle, PosterURL, Overview, ReleaseYear, IsSeries) 
                            VALUES (?, ?, ?, ?, ?, ?, 1)
                        """, (movie_id, name, original_name, poster, overview, year))
                        
                        for genre_id in item.get('genre_ids', []):
                            try:
                                cursor.execute("INSERT INTO Movie_Genre (MovieID, GenreID) VALUES (?, ?)", (movie_id, genre_id))
                            except Exception:
                                pass
                        
                        page_added += 1
                        total_added += 1
                        print(f"   [OK] {name}")
                except Exception as e:
                    print(f"   [LỖI SQL] {item.get('name')}: {e}")
            
            conn.commit()
            print(f"✅ Xong trang {page}: Thêm {page_added} series.")
        except Exception as e:
            print(f"❌ Lỗi gọi API trang {page}: {e}")
        time.sleep(0.5)
        
    conn.close()
    print(f"✔️ HOÀN TẤT PHIM BỘ! Tổng số: {total_added}")

if __name__ == "__main__":
    print("🚀 BẮT ĐẦU CÀO DATA TIẾNG ANH...")
    crawl_movies(pages=30)
    crawl_series(pages=30)
    print("\n🎉 DONE ALL!")