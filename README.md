# 🎬 SmartFlix - Nền tảng Xem phim & Đề xuất AI

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![SQL Server](https://img.shields.io/badge/SQL_Server-CC292B?logo=microsoft-sql-server&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black)
![Scikit-Learn](https://img.shields.io/badge/scikit--learn-%23F7931E.svg?logo=scikit-learn&logoColor=white)

## 📖 Giới thiệu
**SmartFlix** là một ứng dụng web xem phim Full Stack toàn diện. Không chỉ dừng lại ở các tính năng xem phim tiêu chuẩn, nền tảng này còn được tích hợp hệ thống AI gợi ý phim sử dụng thuật toán **K-Means Clustering** và **NLP (TF-IDF)** để phân tích nội dung phim và đề xuất các bộ phim tương tự cho người dùng.

## ✨ Tính năng nổi bật
* **🔐 Xác thực & Quản lý tài khoản:** Đăng ký/Đăng nhập bảo mật, đổi mật khẩu và hỗ trợ tạo tối đa 5 hồ sơ (profiles) riêng biệt cho mỗi tài khoản.
* **🎥 Trải nghiệm Xem phim:** Trình phát video mượt mà hỗ trợ nhiều server, tự động tải danh sách tập phim cho Phim bộ (Series).
* **🤖 Đề xuất AI thông minh:** Gợi ý "Phim tương tự" (More Like This) dựa trên công nghệ học máy (K-Means clustering).
* **📚 Phân loại nội dung động:** Tự động tạo các danh mục (Mới & Phổ biến, Top 10, Duyệt theo ngôn ngữ) và lọc theo thể loại.
* **⭐ Cá nhân hóa trải nghiệm:** Theo dõi Lịch sử xem, "Danh sách của tôi" (Watchlist), và Phim Yêu thích riêng biệt cho từng hồ sơ.
* **🔍 Tìm kiếm thời gian thực:** Tìm kiếm phim nhanh chóng theo từ khóa.

## 🛠️ Công nghệ sử dụng
* **Frontend:** HTML5, CSS3, Vanilla JavaScript.
* **Backend:** Python, FastAPI.
* **Cơ sở dữ liệu:** Microsoft SQL Server.
* **Machine Learning & Data ETL:** Pandas, Scikit-Learn (TF-IDF, K-Means), PyODBC.
* **API Bên ngoài:** TMDB API (Dùng để lấy metadata phong phú và ảnh dự phòng).


## 🚀 Hướng dẫn cài đặt (Chạy Local)

### 1. Thiết lập Database
1. Mở **SQL Server Management Studio (SSMS)**.
2. Mở file `database/SmartFlix_Database_Setup.sql` và chạy (Execute) để tạo database `SmartFlix` cùng toàn bộ các bảng.

### 2. Thiết lập Backend
1. Mở Terminal tại thư mục gốc của dự án.
2. Cài đặt các thư viện Python cần thiết:
```bash
   pip install -r requirements.txt
   ```
3. Tạo một file `.env` ở thư mục gốc và cấu hình thông tin kết nối SQL Server của bạn:
```env
   DB_SERVER=TEN_SERVER_CUA_BAN
   DB_NAME=SmartFlix
   ```
4. Khởi động server FastAPI:
```bash
   uvicorn backend.main:app --reload
   ```

### 3. Thiết lập Frontend
Giao diện Frontend được phục vụ trực tiếp thông qua FastAPI (Static Files). Sau khi Backend đã chạy, bạn chỉ cần mở trình duyệt và truy cập vào đường dẫn sau:
```text
[http://127.0.0.1:8000](http://127.0.0.1:8000)
```
