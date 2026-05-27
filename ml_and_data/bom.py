import pyodbc
import requests
import time

TMDB_API_KEY = "145a8c38c7b2182c288c6fde2be10905"

def get_db_connection():
    # 🛑 Nhớ kiểm tra lại chuỗi này cho khớp nhé
    conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=VINI\\CLCCSDLPTNHOM3;DATABASE=SmartFlix;Trusted_Connection=yes;"
    return pyodbc.connect(conn_str)

def crawl_missing_genres():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("🚀 Bắt đầu chiến dịch rải thảm bơm data cho các Thể loại bị thiếu...")
    
    # Danh sách các thể loại dễ bị "đói" data (ID lấy từ file HTML của ông)
    targets = [
        {"id": 10768, "type": "tv", "is_series": 1, "name": "War & Politics (Series)"},
        {"id": 99, "type": "tv", "is_series": 1, "name": "Documentary (Series)"},
        {"id": 10764, "type": "tv", "is_series": 1, "name": "Reality (Series)"},
        {"id": 37, "type": "tv", "is_series": 1, "name": "Western (Series)"},
        {"id": 36, "type": "movie", "is_series": 0, "name": "History (Movie)"},
        {"id": 10402, "type": "movie", "is_series": 0, "name": "Music (Movie)"},
        {"id": 37, "type": "movie", "is_series": 0, "name": "Western (Movie)"}
    ]
    
    total_added = 0
    
    for target in targets:
        print(f"\n🔍 Đang lùng sục thể loại: {target['name']}")
        
        # Gọi API ép cứng phải tìm đúng cái GenreID đó
        url = f"https://api.themoviedb.org/3/discover/{target['type']}?api_key={TMDB_API_KEY}&with_genres={target['id']}&language=en-VN&page=1"
        res = requests.get(url)
        if res.status_code != 200: continue
        
        data = res.json()
        for item in data.get('results', []):
            movie_id = item['id']
            title = item.get('title') or item.get('name', '')
            overview = item.get('overview', '')
            date_str = item.get('release_date') or item.get('first_air_date', '')
            year = date_str[:4] if date_str else None
            poster = f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get('poster_path') else None
            
            if not poster: continue
            
            # Kiểm tra xem phim đã có chưa
            cursor.execute("SELECT MovieID FROM Movies WHERE MovieID = ?", (movie_id,))
            if not cursor.fetchone():
                try:
                    cursor.execute("""
                        INSERT INTO Movies (MovieID, Title, Overview, ReleaseYear, PosterURL, IsSeries, AgeRating)
                        VALUES (?, ?, ?, ?, ?, ?, 'T16')
                    """, (movie_id, title, overview, year, poster, target['is_series']))
                    
                    # Gắn đủ các thẻ thể loại cho phim đó
                    for genre_id in item.get('genre_ids', []):
                        try:
                            cursor.execute("INSERT INTO Movie_Genre (MovieID, GenreID) VALUES (?, ?)", (movie_id, genre_id))
                        except: pass
                        
                    conn.commit()
                    total_added += 1
                    print(f"  ➕ Thêm thành công: {title}")
                except Exception as e:
                    pass
        time.sleep(0.5) # Tránh bị ban IP

    conn.close()
    print(f"\n🎉 HOÀN TẤT! Đã bơm khẩn cấp {total_added} bộ phim đặc trị vào Database!")

if __name__ == "__main__":
    crawl_missing_genres()