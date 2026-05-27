-- ======================================================
-- DATABASE SCRIPT: SMARTFLIX
-- ======================================================
CREATE DATABASE SmartFlix;
GO

USE SmartFlix;
GO

-- 1. Bảng Users (Tài khoản người dùng)
CREATE TABLE Users (
    UserID INT IDENTITY(1,1) PRIMARY KEY,
    Username NVARCHAR(50) NOT NULL,
    Email NVARCHAR(100) NOT NULL UNIQUE,
    PasswordHash NVARCHAR(255) NOT NULL,
    Role NVARCHAR(20) DEFAULT 'User',
    CreatedAt DATETIME DEFAULT GETDATE()
);

-- 2. Bảng Profiles (Hồ sơ người dùng)
CREATE TABLE Profiles (
    ProfileID INT IDENTITY(1,1) PRIMARY KEY,
    UserID INT NOT NULL FOREIGN KEY REFERENCES Users(UserID),
    ProfileName NVARCHAR(50) NOT NULL,
    AvatarURL VARCHAR(255) DEFAULT 'https://upload.wikimedia.org/wikipedia/commons/0/0b/Netflix-avatar.png',
    IsKid BIT DEFAULT 0
);

-- 3. Bảng Clusters (Phân cụm AI)
CREATE TABLE Clusters (
    ClusterID INT PRIMARY KEY,
    ClusterName NVARCHAR(100),
    Description NVARCHAR(MAX)
);

-- 4. Bảng Genres (Thể loại phim)
CREATE TABLE Genres (
    GenreID INT PRIMARY KEY,
    GenreName NVARCHAR(100) NOT NULL
);

-- 5. Bảng Movies (Kho phim)
CREATE TABLE Movies (
    MovieID INT PRIMARY KEY,
    Title NVARCHAR(MAX) NOT NULL,
    OriginalTitle NVARCHAR(MAX) NULL,
    Overview NVARCHAR(MAX) NULL,
    ReleaseYear INT NULL,
    PosterURL NVARCHAR(MAX) NULL,
    TrailerURL NVARCHAR(MAX) NULL,
    ClusterID INT NULL FOREIGN KEY REFERENCES Clusters(ClusterID),
    IsSeries BIT DEFAULT 0,
    AgeRating VARCHAR(10) NULL,
    OriginalLanguage VARCHAR(10) NULL
);

-- 6. Bảng Movie_Genre (Bảng trung gian Phim - Thể loại)
CREATE TABLE Movie_Genre (
    MovieID INT NOT NULL FOREIGN KEY REFERENCES Movies(MovieID),
    GenreID INT NOT NULL FOREIGN KEY REFERENCES Genres(GenreID),
    PRIMARY KEY (MovieID, GenreID)
);

-- 7. Bảng Favorites (Danh sách yêu thích)
CREATE TABLE Favorites (
    ProfileID INT NOT NULL FOREIGN KEY REFERENCES Profiles(ProfileID),
    MovieID INT NOT NULL FOREIGN KEY REFERENCES Movies(MovieID),
    LikedDate DATETIME DEFAULT GETDATE(),
    PRIMARY KEY (ProfileID, MovieID)
);

-- 8. Bảng Watchlist (Danh sách xem sau / My List)
CREATE TABLE Watchlist (
    ProfileID INT NOT NULL FOREIGN KEY REFERENCES Profiles(ProfileID),
    MovieID INT NOT NULL FOREIGN KEY REFERENCES Movies(MovieID),
    AddedDate DATETIME DEFAULT GETDATE(),
    PRIMARY KEY (ProfileID, MovieID)
);

-- 9. Bảng WatchHistory (Lịch sử xem phim)
CREATE TABLE WatchHistory (
    HistoryID INT IDENTITY(1,1) PRIMARY KEY,
    ProfileID INT NOT NULL FOREIGN KEY REFERENCES Profiles(ProfileID),
    MovieID INT NOT NULL FOREIGN KEY REFERENCES Movies(MovieID),
    WatchedAt DATETIME DEFAULT GETDATE()
);
GO