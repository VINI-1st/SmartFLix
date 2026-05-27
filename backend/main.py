import os
import pyodbc
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from fastapi.staticfiles import StaticFiles

# Tải các biến môi trường từ file .env
load_dotenv()

app = FastAPI(title="SmartFlix API")

# Cấu hình CORS để Frontend và Backend kết nối mượt mà
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# CẤU HÌNH KẾT NỐI CƠ SỞ DỮ LIỆU (SQL SERVER)
# ==========================================
def get_db_connection():
    SERVER_NAME = os.getenv("DB_SERVER", "VINI\\CLCCSDLPTNHOM3")
    DATABASE_NAME = os.getenv("DB_NAME", "SmartFlix")
    conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER_NAME};DATABASE={DATABASE_NAME};Trusted_Connection=yes;"
    return pyodbc.connect(conn_str)


# ==========================================
# CÁC MÔ HÌNH DỮ LIỆU (PYDANTIC MODELS)
# ==========================================
class UserAction(BaseModel):
    profile_id: int
    movie_id: int

class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class ProfileCreate(BaseModel):
    user_id: int
    profile_name: str
    avatar_url: Optional[str] = "https://upload.wikimedia.org/wikipedia/commons/0/0b/Netflix-avatar.png"

class EmailUpdate(BaseModel):
    new_email: str

class PasswordUpdate(BaseModel):
    old_password: str  # Đồng bộ chính xác với old_password của account.html
    new_password: str


# ==========================================
# 1. HỆ THỐNG XÁC THỰC (AUTH)
# ==========================================
@app.post("/api/register")
def register_user(user: UserRegister):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM Users WHERE Email = ?", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already exists.")
        
        cursor.execute(
            "INSERT INTO Users (Username, Email, PasswordHash) VALUES (?, ?, ?)",
            (user.username, user.email, user.password)
        )
        conn.commit()
        return {"status": "success", "message": "User registered successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.post("/api/login")
def login_user(user: UserLogin):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT UserID, Username, Email, Role FROM Users WHERE Email = ? AND PasswordHash = ?", (user.email, user.password))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        
        return {
            "status": "success",
            "user": {
                "id": row.UserID,
                "username": row.Username,
                "email": row.Email,
                "role": row.Role
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.put("/api/users/{user_id}/email")
def update_email(user_id: int, data: EmailUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Users SET Email = ? WHERE UserID = ?", (data.new_email, user_id))
        conn.commit()
        return {"status": "success", "message": "Email updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.put("/api/users/{user_id}/password")
def update_password(user_id: int, data: PasswordUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM Users WHERE UserID = ? AND PasswordHash = ?", (user_id, data.old_password))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Incorrect current password.")
            
        cursor.execute("UPDATE Users SET PasswordHash = ? WHERE UserID = ?", (data.new_password, user_id))
        conn.commit()
        return {"status": "success", "message": "Password updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


# ==========================================
# 2. HỆ THỐNG QUẢN LÝ HỒ SƠ (PROFILES)
# ==========================================
def fetch_profiles_shared_logic(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT ProfileID, ProfileName, AvatarURL FROM Profiles WHERE UserID = ?", (user_id,))
        rows = cursor.fetchall()
        
        profiles = []
        for row in rows:
            profiles.append({
                "id": row.ProfileID,
                "profile_id": row.ProfileID,
                "ProfileID": row.ProfileID,
                "name": row.ProfileName,
                "profile_name": row.ProfileName,
                "ProfileName": row.ProfileName,
                "avatar_url": row.AvatarURL,
                "AvatarURL": row.AvatarURL
            })
        return {
            "status": "success",
            "data": profiles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/users/{user_id}/profiles")
def get_user_profiles_v1(user_id: int):
    return fetch_profiles_shared_logic(user_id)

@app.get("/api/profiles/{user_id}")
def get_user_profiles_v2(user_id: int):
    return fetch_profiles_shared_logic(user_id)

@app.post("/api/profiles")
def create_profile(profile: ProfileCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM Profiles WHERE UserID = ?", (profile.user_id,))
        if cursor.fetchone()[0] >= 5:
            raise HTTPException(status_code=400, detail="Maximum of 5 profiles reached.")
            
        cursor.execute(
            "INSERT INTO Profiles (UserID, ProfileName, AvatarURL) VALUES (?, ?, ?)",
            (profile.user_id, profile.profile_name, profile.avatar_url)
        )
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.delete("/api/profiles/{profile_id}")
def delete_profile(profile_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        tables_to_clear = ["Watchlist", "Favorites", "WatchHistory"]
        for table in tables_to_clear:
            try:
                cursor.execute(f"DELETE FROM {table} WHERE ProfileID = ?", (profile_id,))
            except Exception:
                try:
                    cursor.execute(f"DELETE FROM {table} WHERE UserID = ?", (profile_id,))
                except Exception:
                    pass 
                    
        cursor.execute("DELETE FROM Profiles WHERE ProfileID = ?", (profile_id,))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


# ==========================================
# 3. DANH SÁCH PHIM & ĐỀ XUẤT AI (MOVIES)
# ==========================================
@app.get("/api/movies")
def get_popular_movies():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # [FIX]: Tăng lên 100 và trộn ngẫu nhiên để JS chia mảng không bị rỗng
        cursor.execute("SELECT TOP 100 MovieID, Title, PosterURL, TrailerURL, Overview, ReleaseYear, IsSeries, AgeRating FROM Movies ORDER BY NEWID()")
        rows = cursor.fetchall()
        movies = []
        for row in rows:
            movies.append({
                "id": row.MovieID, "title": row.Title, "poster": row.PosterURL, 
                "trailer": row.TrailerURL, "overview": row.Overview, "year": row.ReleaseYear, 
                "IsSeries": row.IsSeries, "age_rating": row.AgeRating
            })
        return movies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/movies/random")
def get_trendy_hero_banner(type: str = "popular"):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Tạo điều kiện lọc (Mẹo dùng 1=1 để nối chuỗi AND cho mượt)
        condition = "1=1" 
        if type == "tv":
            condition += " AND IsSeries = 1"
        elif type == "movie":
            condition += " AND (IsSeries = 0 OR IsSeries IS NULL)"
            
        # 2. KHÔNG FIX SỐ LƯỢNG NỮA: Lấy ngẫu nhiên phim sản xuất trong 2 năm trở lại đây
        # Hàm YEAR(GETDATE()) sẽ lấy năm hiện tại, trừ đi 2 để ra mốc thời gian.
        query = f"""
            SELECT TOP 1 MovieID, Title, PosterURL, TrailerURL, Overview, ReleaseYear, IsSeries, AgeRating
            FROM Movies
            WHERE {condition} AND ReleaseYear >= YEAR(GETDATE()) - 2
            ORDER BY NEWID()
        """
        cursor.execute(query)
        row = cursor.fetchone()
        
        if row:
            return {
                "id": row.MovieID, "title": row.Title, "poster": row.PosterURL,
                "trailer": row.TrailerURL, "overview": row.Overview, 
                "year": row.ReleaseYear, "IsSeries": row.IsSeries, "age_rating": row.AgeRating
            }
        return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
@app.get("/api/movies/genre/{genre_id}")
def get_movies_by_genre(genre_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT m.MovieID, m.Title, m.PosterURL, m.TrailerURL, m.Overview, m.ReleaseYear, m.IsSeries, m.AgeRating
            FROM Movie_Genre mg
            JOIN Movies m ON mg.MovieID = m.MovieID
            WHERE mg.GenreID = ? AND m.IsSeries = 0
        """
        cursor.execute(query, (genre_id,))
        rows = cursor.fetchall()
        movies = []
        for row in rows:
            movies.append({
                "id": row.MovieID, "title": row.Title, "poster": row.PosterURL, 
                "trailer": row.TrailerURL, "overview": row.Overview, "year": row.ReleaseYear, 
                "IsSeries": row.IsSeries, "age_rating": row.AgeRating
            })
        return movies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/series/genre/{genre_id}")
def get_series_by_genre(genre_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT m.MovieID, m.Title, m.PosterURL, m.TrailerURL, m.Overview, m.ReleaseYear, m.IsSeries, m.AgeRating
            FROM Movie_Genre mg
            JOIN Movies m ON mg.MovieID = m.MovieID
            WHERE mg.GenreID = ? AND m.IsSeries = 1
        """
        cursor.execute(query, (genre_id,))
        rows = cursor.fetchall()
        series = []
        for row in rows:
            series.append({
                "id": row.MovieID, "title": row.Title, "poster": row.PosterURL, 
                "trailer": row.TrailerURL, "overview": row.Overview, "year": row.ReleaseYear, 
                "IsSeries": row.IsSeries, "age_rating": row.AgeRating
            })
        return series
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ==========================================
# [FIX]: BỔ SUNG HÀM TÌM KIẾM BỊ THIẾU
# ==========================================
@app.get("/api/search")
def search_movies(q: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT TOP 20 MovieID, Title, PosterURL, TrailerURL, Overview, ReleaseYear, IsSeries, AgeRating FROM Movies WHERE Title LIKE ?", (f"%{q}%",))
        rows = cursor.fetchall()
        movies = []
        for row in rows:
            movies.append({
                "id": row.MovieID, "title": row.Title, "poster": row.PosterURL, 
                "trailer": row.TrailerURL, "overview": row.Overview, "year": row.ReleaseYear, 
                "IsSeries": row.IsSeries, "age_rating": row.AgeRating
            })
        return movies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/recommend/{movie_id}")
def get_ai_recommendations(movie_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT ClusterID FROM Movies WHERE MovieID = ?", (movie_id,))
        row = cursor.fetchone()
        
        # 1. CHỐNG BẪY SỐ 0: Dùng "is None" thay vì "not row.ClusterID"
        if not row or row.ClusterID is None:
            cursor.execute("SELECT TOP 10 MovieID, Title, PosterURL, TrailerURL, Overview, ReleaseYear, IsSeries, AgeRating FROM Movies ORDER BY NEWID()")
        else:
            cursor.execute("SELECT TOP 10 MovieID, Title, PosterURL, TrailerURL, Overview, ReleaseYear, IsSeries, AgeRating FROM Movies WHERE ClusterID = ? AND MovieID != ? ORDER BY NEWID()", (row.ClusterID, movie_id))
            
        rows = cursor.fetchall()
        
        # 2. CHỐNG BẪY CỤM CÔ ĐƠN: 
        # Nếu cụm K-Means này bị rỗng (do phim đứng 1 mình), lập tức bốc phim cùng Thể Loại (Genre) lấp vào để web không bao giờ bị đen xì!
        if len(rows) == 0:
            cursor.execute("""
                SELECT TOP 10 m.MovieID, m.Title, m.PosterURL, m.TrailerURL, m.Overview, m.ReleaseYear, m.IsSeries, m.AgeRating 
                FROM Movie_Genre mg
                JOIN Movies m ON mg.MovieID = m.MovieID
                WHERE mg.GenreID IN (SELECT GenreID FROM Movie_Genre WHERE MovieID = ?) AND m.MovieID != ?
                ORDER BY NEWID()
            """, (movie_id, movie_id))
            rows = cursor.fetchall()
            
            # Fallback đường cùng: Bốc random nếu phim chả có thể loại nào
            if len(rows) == 0:
                cursor.execute("SELECT TOP 10 MovieID, Title, PosterURL, TrailerURL, Overview, ReleaseYear, IsSeries, AgeRating FROM Movies WHERE MovieID != ? ORDER BY NEWID()", (movie_id,))
                rows = cursor.fetchall()

        movies = []
        for r in rows:
            movies.append({
                "id": r.MovieID, "title": r.Title, "poster": r.PosterURL, 
                "trailer": r.TrailerURL, "overview": r.Overview, "year": r.ReleaseYear, 
                "IsSeries": r.IsSeries, "age_rating": r.AgeRating
            })
        return {"recommendations": movies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
    
# ==========================================
# 4. LỊCH SỬ XEM (WATCH HISTORY)
# ==========================================
@app.post("/api/history")
def save_watch_history(action: UserAction):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Kiểm tra xem Profile này đã xem phim này chưa
        cursor.execute("SELECT 1 FROM WatchHistory WHERE ProfileID = ? AND MovieID = ?", (action.profile_id, action.movie_id))
        
        if cursor.fetchone():
            # Nếu đã xem -> Cập nhật lại thời gian xem thành mới nhất (GETDATE) để phim ngoi lên đầu
            cursor.execute("UPDATE WatchHistory SET WatchedAt = GETDATE() WHERE ProfileID = ? AND MovieID = ?", (action.profile_id, action.movie_id))
        else:
            # Nếu chưa xem -> Thêm mới bản ghi
            cursor.execute("INSERT INTO WatchHistory (ProfileID, MovieID) VALUES (?, ?)", (action.profile_id, action.movie_id))
        
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        print(f"LỖI LƯU LỊCH SỬ TỪ DB: {str(e)}") # In lỗi ra console uvicorn để dễ bắt bệnh
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/history/{profile_id}")
def get_watch_history(profile_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Sắp xếp WatchedAt giảm dần (DESC)
        query = """
            SELECT m.MovieID, m.Title, m.PosterURL, m.TrailerURL, m.Overview, m.ReleaseYear, m.IsSeries, m.AgeRating
            FROM WatchHistory wh
            JOIN Movies m ON wh.MovieID = m.MovieID
            WHERE wh.ProfileID = ?
            ORDER BY wh.WatchedAt DESC
        """
        cursor.execute(query, (profile_id,))
        rows = cursor.fetchall()
        
        movies = []
        for row in rows:
            movies.append({
                "id": row.MovieID, 
                "title": row.Title, 
                "poster": row.PosterURL, 
                "trailer": row.TrailerURL, 
                "overview": row.Overview, 
                "year": row.ReleaseYear, 
                "IsSeries": row.IsSeries, 
                "age_rating": row.AgeRating
            })
        return movies
    except Exception as e:
        print(f"LỖI TẢI LỊCH SỬ TỪ DB: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.post("/api/watchlist")
def toggle_watchlist(action: UserAction):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        try:
            cursor.execute("SELECT 1 FROM Watchlist WHERE ProfileID = ? AND MovieID = ?", (action.profile_id, action.movie_id))
            if cursor.fetchone():
                cursor.execute("DELETE FROM Watchlist WHERE ProfileID = ? AND MovieID = ?", (action.profile_id, action.movie_id))
                conn.commit()
                return {"status": "removed", "message": "Removed from My List"}
            
            cursor.execute("INSERT INTO Watchlist (ProfileID, MovieID) VALUES (?, ?)", (action.profile_id, action.movie_id))
            conn.commit()
            return {"status": "added", "message": "Added to My List"}
        except Exception:
            # [FIX]: Fallback Database cũ
            cursor.execute("SELECT 1 FROM Watchlist WHERE UserID = ? AND MovieID = ?", (action.profile_id, action.movie_id))
            if cursor.fetchone():
                cursor.execute("DELETE FROM Watchlist WHERE UserID = ? AND MovieID = ?", (action.profile_id, action.movie_id))
                conn.commit()
                return {"status": "removed", "message": "Removed from My List"}
            
            cursor.execute("INSERT INTO Watchlist (UserID, MovieID) VALUES (?, ?)", (action.profile_id, action.movie_id))
            conn.commit()
            return {"status": "added", "message": "Added to My List"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.get("/api/watchlist/{profile_id}")
def get_watchlist(profile_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        try:
            query = """
                SELECT m.MovieID, m.Title, m.PosterURL, m.TrailerURL, m.ReleaseYear, m.IsSeries, m.AgeRating
                FROM Watchlist w
                JOIN Movies m ON w.MovieID = m.MovieID
                WHERE w.ProfileID = ?
            """
            cursor.execute(query, (profile_id,))
        except Exception:
            # [FIX]: Fallback Database cũ
            query = """
                SELECT m.MovieID, m.Title, m.PosterURL, m.TrailerURL, m.ReleaseYear, m.IsSeries, m.AgeRating
                FROM Watchlist w
                JOIN Movies m ON w.MovieID = m.MovieID
                WHERE w.UserID = ?
            """
            cursor.execute(query, (profile_id,))
            
        rows = cursor.fetchall()
        movies = []
        for row in rows:
            movies.append({
                "id": row.MovieID, "title": row.Title, "poster": row.PosterURL, 
                "trailer": row.TrailerURL, "year": row.ReleaseYear, 
                "IsSeries": row.IsSeries, "age_rating": row.AgeRating
            })
        return movies
    except Exception as e:
        return []
    finally:
        conn.close()

@app.post("/api/favorites")
def toggle_favorite(action: UserAction):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        try:
            cursor.execute("SELECT 1 FROM Favorites WHERE ProfileID = ? AND MovieID = ?", (action.profile_id, action.movie_id))
            if cursor.fetchone():
                cursor.execute("DELETE FROM Favorites WHERE ProfileID = ? AND MovieID = ?", (action.profile_id, action.movie_id))
                conn.commit()
                return {"status": "removed"}
            else:
                cursor.execute("INSERT INTO Favorites (ProfileID, MovieID) VALUES (?, ?)", (action.profile_id, action.movie_id))
                conn.commit()
                return {"status": "added"}
        except Exception:
            # [FIX]: Fallback Database cũ
            cursor.execute("SELECT 1 FROM Favorites WHERE UserID = ? AND MovieID = ?", (action.profile_id, action.movie_id))
            if cursor.fetchone():
                cursor.execute("DELETE FROM Favorites WHERE UserID = ? AND MovieID = ?", (action.profile_id, action.movie_id))
                conn.commit()
                return {"status": "removed"}
            else:
                cursor.execute("INSERT INTO Favorites (UserID, MovieID) VALUES (?, ?)", (action.profile_id, action.movie_id))
                conn.commit()
                return {"status": "added"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.get("/api/favorites/{profile_id}")
def get_user_favorites(profile_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        try:
            cursor.execute("""
                SELECT m.MovieID, m.Title, m.PosterURL, m.TrailerURL, m.Overview, m.ReleaseYear, m.IsSeries, m.AgeRating 
                FROM Favorites f
                JOIN Movies m ON f.MovieID = m.MovieID 
                WHERE f.ProfileID = ?
                ORDER BY f.LikedAt DESC 
            """, (profile_id,))
        except Exception:
            # [FIX]: Fallback Database cũ
            cursor.execute("""
                SELECT m.MovieID, m.Title, m.PosterURL, m.TrailerURL, m.Overview, m.ReleaseYear, m.IsSeries, m.AgeRating 
                FROM Favorites f
                JOIN Movies m ON f.MovieID = m.MovieID 
                WHERE f.UserID = ?
                ORDER BY f.LikedAt DESC 
            """, (profile_id,))
            
        rows = cursor.fetchall()
        movies = []
        for row in rows:
            movies.append({
                "id": row.MovieID, "title": row.Title, "poster": row.PosterURL, 
                "trailer": row.TrailerURL, "overview": row.Overview, "year": row.ReleaseYear, 
                "IsSeries": row.IsSeries, "age_rating": row.AgeRating
            })
        return movies
    except Exception as e:
        return []
    finally:
        conn.close()

@app.get("/api/movies/language/{lang_code}")
def get_movies_by_language(lang_code: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Truy vấn Real Data từ SQL Server
        query = """
            SELECT MovieID, Title, PosterURL, TrailerURL, Overview, ReleaseYear, IsSeries, AgeRating
            FROM Movies
            WHERE OriginalLanguage = ?
            ORDER BY ReleaseYear DESC
        """
        cursor.execute(query, (lang_code,))
        rows = cursor.fetchall()
        
        movies = []
        for row in rows:
            movies.append({
                "id": row.MovieID, "title": row.Title, "poster": row.PosterURL, 
                "trailer": row.TrailerURL, "overview": row.Overview, "year": row.ReleaseYear, 
                "IsSeries": row.IsSeries, "age_rating": row.AgeRating
            })
        return movies
    except Exception as e:
        # Import HTTPException từ fastapi nếu file chưa có
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
# ==========================================
# CẤU HÌNH ĐỊNH TUYẾN GIAO DIỆN (FRONTEND)
# ==========================================
@app.get("/")
def redirect_to_login():
    return RedirectResponse(url="/login.html")

# Tự động lấy đường dẫn của thư mục gốc WEB_XEMPHIM và trỏ vào frontend
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_path = os.path.join(base_dir, "frontend")

# Dòng phát tài nguyên tĩnh
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)