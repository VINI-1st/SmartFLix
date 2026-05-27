import os
import pyodbc
import pandas as pd
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG
# ==========================================
load_dotenv()

def get_db_connection():
    SERVER_NAME = os.getenv("DB_SERVER", "VINI\\CLCCSDLPTNHOM3")
    DATABASE_NAME = os.getenv("DB_NAME", "SmartFlix")
    conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER_NAME};DATABASE={DATABASE_NAME};Trusted_Connection=yes;"
    return pyodbc.connect(conn_str)

def train_ai():
    try:
        print("🔌 1. Kết nối cơ sở dữ liệu...")
        conn = get_db_connection()
        
        print("📥 2. Đọc dữ liệu Phim và Thể loại từ CSDL...")
        # Lấy chéo sang bảng Movie_Genre và Genres để lấy tên Thể loại
        query = """
            SELECT m.MovieID, m.Title, m.Overview, g.GenreName
            FROM Movies m
            LEFT JOIN Movie_Genre mg ON m.MovieID = mg.MovieID
            LEFT JOIN Genres g ON mg.GenreID = g.GenreID
        """
        df_raw = pd.read_sql(query, conn)
        
        if df_raw.empty:
            print("❌ Không có dữ liệu phim!")
            return

        print("🧹 3. Đang tiền xử lý và nhồi thêm Thể loại...")
        # Một phim có nhiều thể loại -> Gộp chúng thành 1 chuỗi (VD: "Action Sci-Fi")
        df = df_raw.groupby(['MovieID', 'Title', 'Overview'], dropna=False)['GenreName'].apply(lambda x: ' '.join(x.dropna())).reset_index()
        
        # Vá các lỗ hổng dữ liệu bị NULL
        df['Overview'] = df['Overview'].fillna('')
        df['GenreName'] = df['GenreName'].fillna('')
        
        # 🛑 BÍ KÍP DATA SCIENCE: Nhân 3 lần chuỗi Thể loại để tăng trọng số tuyệt đối cho K-Means
        # Ví dụ: "Action Sci-Fi Action Sci-Fi Action Sci-Fi" -> TF-IDF sẽ dồn điểm cực cao cho 2 từ này
        df['Cleaned_Text'] = df['Title'] + " " + df['Overview'] + " " + (df['GenreName'] + " ") * 3

        print("🧠 4. Đang chạy thuật toán K-Means (Chia thành 20 Cụm)...")
        # Sử dụng TF-IDF để chuyển chữ thành ma trận số học
        tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
        tfidf_matrix = tfidf.fit_transform(df['Cleaned_Text'])

        num_clusters = 20
        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
        df['ClusterID'] = kmeans.fit_predict(tfidf_matrix)

        print("💾 5. Đang lưu kết quả AI vào Database...")
        cursor = conn.cursor()
        
        cursor.execute("UPDATE Movies SET ClusterID = NULL")
        cursor.execute("DELETE FROM Clusters")
        
        print("   -> Đang khởi tạo 20 Cụm mới...")
        for i in range(num_clusters):
            cluster_name = f"Cluster {i}"
            desc = f"Movies with similar plots and genres (AI generated group {i})"
            cursor.execute("INSERT INTO Clusters (ClusterID, ClusterName, Description) VALUES (?, ?, ?)", (i, cluster_name, desc))
            
        print(f"   -> Đang dán nhãn Cụm cho {len(df)} bộ phim...")
        update_query = "UPDATE Movies SET ClusterID = ? WHERE MovieID = ?"
        
        update_data = [(int(row['ClusterID']), int(row['MovieID'])) for index, row in df.iterrows()]
        cursor.executemany(update_query, update_data)
            
        conn.commit()
        print("🎉 HOÀN TẤT! AI đã học xong kết hợp cả Cốt truyện và Thể loại.")

    except Exception as e:
        print(f"❌ Lỗi: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    train_ai()