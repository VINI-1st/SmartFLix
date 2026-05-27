import os
import pyodbc
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

# 1. Cấu hình Database
load_dotenv()
SERVER_NAME = os.getenv("DB_SERVER") 
DATABASE_NAME = os.getenv("DB_NAME")
conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER_NAME};DATABASE={DATABASE_NAME};Trusted_Connection=yes;"

def find_elbow():
    print("🔌 1. Kết nối cơ sở dữ liệu...")
    conn = pyodbc.connect(conn_str)
    query = "SELECT MovieID, Title, Overview FROM Movies WHERE Overview IS NOT NULL AND Overview != ''"
    df = pd.read_sql(query, conn)
    conn.close()

    print(f"🧠 2. Đang xử lý NLP (TF-IDF) cho {len(df)} bộ phim...")
    tfidf = TfidfVectorizer(max_features=5000)
    tfidf_matrix = tfidf.fit_transform(df['Overview'])

    print("⏳ 3. Đang chạy K-Means thử nghiệm từ 2 đến 40 cụm (Quá trình này mất khoảng 1-2 phút)...")
    wcss = []
    # Chạy thử các giá trị K chẵn từ 2 đến 40 để tiết kiệm thời gian
    K_range = range(2, 42, 2) 
    
    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(tfidf_matrix)
        wcss.append(kmeans.inertia_) # inertia_ chính là giá trị WCSS
        print(f"   -> Đã tính xong WCSS cho K = {k}")

    print("📊 4. Đang vẽ biểu đồ Elbow...")
    plt.figure(figsize=(10, 6))
    plt.plot(K_range, wcss, marker='o', linestyle='-', color='b')
    plt.title('Phương pháp Elbow: Tìm số cụm tối ưu cho K-Means')
    plt.xlabel('Số lượng cụm (K)')
    plt.ylabel('Giá trị WCSS (Độ phân tán)')
    plt.grid(True)
    
    # Lưu biểu đồ thành file ảnh thay vì show lên để tránh lỗi đồ họa trên VS Code
    plt.savefig('elbow_chart.png')
    print("🎉 HOÀN TẤT! Hãy mở file 'elbow_chart.png' vừa được tạo ra để xem điểm cùi chỏ nhé.")

if __name__ == "__main__":
    find_elbow()