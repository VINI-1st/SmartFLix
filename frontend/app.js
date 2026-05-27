const API_BASE = "http://127.0.0.1:8000/api";
const TMDB_API_KEY = "145a8c38c7b2182c288c6fde2be10905";

// ==========================================
// 1. KIỂM TRA ĐĂNG NHẬP & NAVBAR
// ==========================================
const activeProfileId = localStorage.getItem("activeProfileId");
if (!activeProfileId) {
    window.location.href = "profiles.html"; 
}

document.addEventListener("DOMContentLoaded", () => {
    const avatarImg = document.querySelector(".user-profile img"); 
    const activeAvatar = localStorage.getItem("activeProfileAvatar"); 
    if (avatarImg && activeAvatar) {
        avatarImg.src = activeAvatar; 
    }
});

const userStr = localStorage.getItem("smartflix_user");
if (!userStr) {
    window.location.href = "login.html";
} else {
    const currentUser = JSON.parse(userStr);
    const USER_ID = currentUser.id;
}

function logout() {
    localStorage.clear(); 
    window.location.href = "login.html";
}

function switchProfile() {
    localStorage.removeItem("activeProfileId");
    localStorage.removeItem("activeProfileName");
    localStorage.removeItem("activeProfileAvatar");
    window.location.href = "profiles.html";
}

window.addEventListener("scroll", () => {
    const navbar = document.getElementById("navbar");
    if (navbar) {
        if (window.scrollY > 50) navbar.classList.add("scrolled");
        else navbar.classList.remove("scrolled");
    }
});

// ==========================================
// 2. TẠO THẺ PHIM 
// ==========================================
function createMovieCard(movie) {
    const div = document.createElement("div");
    div.className = "movie-card";
    
    // 🛑 BỘ LỌC CHỐNG LỖI UNDEFINED:
    // Thử lấy data từ API, nếu không có hoặc bị lỗi null/undefined thì gán mặc định là T16
    let ratingData = movie.age_rating || movie.AgeRating;
    if (!ratingData || ratingData === "undefined" || ratingData === "null") {
        ratingData = "T16"; 
    }

    div.innerHTML = `
        <img src="${movie.poster}" alt="${movie.title}" title="${movie.title}">
        <div class="card-details">
            <div class="controls">
                <div style="display: flex; gap: 10px;">
                    <button class="btn-card-play" title="Play">▶</button>
                    <button class="btn-card-add" title="Add to My List">+</button>
                </div>
                <button class="btn-card-detail" title="Details">v</button>
            </div>
            <div class="metadata">
                <span class="age-rating">${ratingData}</span>
                <span>${movie.year || "2024"}</span>
            </div>
        </div>
    `;

    div.onclick = () => openMovieDetail(movie);

    const addBtn = div.querySelector('.btn-card-add');
    if (addBtn) {
        addBtn.onclick = (e) => {
            e.stopPropagation(); 
            addToWatchlist(movie.id || movie.MovieID);
        };
    }

    const playBtn = div.querySelector('.btn-card-play');
    if (playBtn) {
        playBtn.onclick = (e) => {
            e.stopPropagation(); 
            const isSeries = movie.IsSeries === 1 || movie.isseries === 1 || movie.IsSeries === true;
            if (isSeries) {
                playSeriesEpisode(movie.id || movie.MovieID, 1, 1);
            } else {
                playMovie(movie.trailer, movie.id || movie.MovieID);
            }
        };
    }

    return div;
}

// ==========================================
// 3. TẢI DỮ LIỆU API
// ==========================================
async function loadMovies() {
    try {
        const response = await fetch(`${API_BASE}/movies`);
        const movies = await response.json();
        
        loadHeroBanner(); 
        
        const container = document.getElementById("movie-list");
        if(container) {
            container.innerHTML = ""; 
            movies.forEach(movie => container.appendChild(createMovieCard(movie)));
        }
    } catch (e) { console.error("Error loading movies:", e); }
}

async function loadWatchHistory() {
    try {
        const response = await fetch(`${API_BASE}/history/${activeProfileId}`);
        const movies = await response.json();
        const container = document.getElementById("history-list");
        if(container) {
            container.innerHTML = movies.length > 0 ? "" : "<p style='color: gray; padding: 20px;'>You haven't watched any movies yet.</p>";
            movies.forEach(movie => container.appendChild(createMovieCard(movie)));
        }
    } catch (e) {
        console.error("Lỗi khi tải lịch sử xem (Watch History):", e);
    }
}

// ==========================================
// QUẢN LÝ DỮ LIỆU MY LIST (CHỈ DÙNG CHO DẤU +)
// ==========================================
async function loadMyListUnified() {
    try {
        // Lần này CHỈ CÀO API watchlist, chia tay API favorites
        const res = await fetch(`${API_BASE}/watchlist/${activeProfileId}`);
        const uniqueMovies = await res.json();

        // 1. Đổ vào Trang Chủ Home
        const homeContainer = document.getElementById("watchlist-home");
        if (homeContainer) {
            homeContainer.innerHTML = uniqueMovies.length > 0 ? "" : "<p style='color: gray; padding: 20px;'>Your list is empty.</p>";
            uniqueMovies.forEach(movie => homeContainer.appendChild(createMovieCard(movie)));
        }

        // 2. Đổ vào Tab My List Riêng (Dạng lưới)
        const pageContainer = document.getElementById("watchlist-page");
        if (pageContainer) {
            pageContainer.innerHTML = uniqueMovies.length > 0 ? "" : "<p style='color: gray; padding: 20px; grid-column: 1 / -1; font-size: 1.2rem;'>Your list is empty.</p>";
            uniqueMovies.forEach(movie => pageContainer.appendChild(createMovieCard(movie)));
        }
    } catch (e) { console.error("Lỗi tải My List:", e); }
}

async function loadWatchlist() { await loadMyListUnified(); }
async function loadFavoriteMovies() { /* Giữ im lặng hoàn toàn để không cướp sóng của My List */ }

// ==========================================
// TÂY HÓA THÔNG BÁO KHI BẤM DẤU (+) VÀ NÚT XÓA
// ==========================================
async function addToWatchlist(movieId) {
    try {
        const res = await fetch(`${API_BASE}/watchlist`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ profile_id: parseInt(activeProfileId), movie_id: movieId })
        });
        const data = await res.json();
        
        // Phân nhánh thông báo chuẩn tiếng Anh
        if (data.status === "added") {
            alert("Added to My List!");
        } else if (data.status === "removed") {
            alert("Removed from My List!");
        }
        
        // Cực kỳ quan trọng: Gọi lại hàm này để load lại danh sách. 
        // Phim nào vừa bị xóa sẽ bốc hơi khỏi màn hình ngay lập tức!
        loadWatchlist(); 
        
    } catch(e) {
        console.error("Lỗi khi thêm/xóa My List:", e);
    }
}

// ==========================================
// HÀM TẢI PHIM LẺ (MOVIES) THEO THỂ LOẠI
// ==========================================
async function loadMoviesByGenre(genreId, elementId) {
    try {
        const response = await fetch(`${API_BASE}/movies/genre/${genreId}`);
        const movies = await response.json();
        const container = document.getElementById(elementId);
        if(container) {
            container.innerHTML = ""; 
            movies.forEach(movie => container.appendChild(createMovieCard(movie)));
        }
    } catch (e) { console.error("Lỗi tải Phim Lẻ:", e); }
}

async function loadSeriesByGenre(genreId, elementId) {
    try {
        const response = await fetch(`${API_BASE}/series/genre/${genreId}`);
        const series = await response.json();
        const container = document.getElementById(elementId);
        if(container) {
            container.innerHTML = ""; 
            series.forEach(movie => container.appendChild(createMovieCard(movie)));
        }
    } catch (e) { console.error("Lỗi tải Series:", e); }
}


// ==========================================
// HÀM HIỂN THỊ BANNER (BỌC THÉP CHỐNG LỖI 100%)
// ==========================================
async function loadHeroBanner(category = "popular") { 
    const heroBanner = document.getElementById("hero-banner");
    const heroTitle = document.getElementById("hero-title");
    const heroDesc = document.getElementById("hero-desc");
    if(!heroBanner) return;     

    let featured;
    try {
        // 1. Gọi API Backend để lấy phim
        const randomRes = await fetch(`${API_BASE}/movies/random?type=${category}`);
        if (!randomRes.ok) throw new Error(`Mã lỗi Server: ${randomRes.status}`);
        featured = await randomRes.json();
    } catch(e) {
        // 🛑 NẾU BACKEND SẬP -> IN THẲNG LỖI RA MÀN HÌNH ĐỂ BẮT BỆNH
        console.error("Lỗi API lấy phim:", e);
        if(heroTitle) heroTitle.innerText = "Lỗi Kết Nối Máy Chủ!";
        if(heroDesc) heroDesc.innerText = "Ông mở ngay cái cửa sổ màu đen đang chạy uvicorn main:app --reload lên xem nó có báo dòng chữ đỏ (Syntax Error / IndentationError) nào không nhé!";
        return; 
    }

    // 2. Gán tên phim chuẩn (Hứng mọi loại key từ API)
    const title = featured.title || featured.Title || "Unknown Movie";
    if(heroTitle) heroTitle.innerText = title;

    const movieId = featured.id || featured.MovieID;
    const isSeries = featured.IsSeries === 1 || featured.isseries === 1 || featured.IsSeries === true;
    
    // 3. Gán sự kiện cho Nút bấm
    const btnThongTin = document.querySelector(".btn-more-info");
    if(btnThongTin) btnThongTin.onclick = () => openMovieDetail(featured);

    const heroPlayBtn = document.getElementById("hero-play-btn");
    if(heroPlayBtn) {
        heroPlayBtn.onclick = () => {
            if (isSeries) {
                playSeriesEpisode(movieId, 1, 1);
            } else {
                playMovie(featured.trailer || featured.TrailerURL, movieId);
            }
        };
    }

    // 4. Gọi TMDB lấy ảnh đẹp (Tìm chuẩn theo Tên)
    try {
        const tmdbType = isSeries ? 'tv' : 'movie';
        
        // Dùng biến TMDB_API_KEY của ông (nếu chưa có thì nó tự bắt lỗi)
        const apiKey = typeof TMDB_API_KEY !== 'undefined' ? TMDB_API_KEY : 'YOUR_API_KEY';
        const searchUrl = `https://api.themoviedb.org/3/search/${tmdbType}?api_key=${apiKey}&query=${encodeURIComponent(title)}&language=en-US`;
        
        const res = await fetch(searchUrl);
        const data = await res.json();
        
        if (data.results && data.results.length > 0) {
            const tmdbMovie = data.results[0]; 
            const bgUrl = tmdbMovie.backdrop_path ? `https://image.tmdb.org/t/p/original${tmdbMovie.backdrop_path}` : (featured.poster || featured.PosterURL);
            heroBanner.style.backgroundImage = `url('${bgUrl}')`;

            let finalOverview = tmdbMovie.overview || featured.overview || featured.Overview || "Overview is currently unavailable.";
            if(heroDesc) heroDesc.innerText = finalOverview.length > 200 ? finalOverview.substring(0, 200) + "..." : finalOverview;
        } else {
            throw new Error("TMDB không tìm ra tên phim này");
        }
    } catch (e) { 
        // 5. BACKUP XỊN: Nếu TMDB gãy, lấy luôn Poster trong SQL làm nền!
        console.warn("Dùng ảnh dự phòng của SQL:", e.message);
        heroBanner.style.backgroundImage = `url('${featured.poster || featured.PosterURL}')`; 
        let fallback = featured.overview || featured.Overview || "Overview is currently unavailable.";
        if(heroDesc) heroDesc.innerText = fallback.length > 200 ? fallback.substring(0, 200) + "..." : fallback;
    }
}

async function openMovieDetail(movie) {
    const modal = document.getElementById("movieModal");
    if(!modal) return;
    modal.style.display = "block";
    document.body.style.overflow = "hidden";

    const movieId = movie.id || movie.MovieID;
    
    const isSeriesMovie = movie.IsSeries === 1 || movie.isseries === 1 || movie.IsSeries === true;
    
    const modalPlayBtn = document.getElementById("modal-play-btn");
    if(modalPlayBtn) {
        modalPlayBtn.onclick = () => {
            if (isSeriesMovie) {
                playSeriesEpisode(movieId, 1, 1);
            } else {
                playMovie(movie.trailer, movieId);
            }
        };
    }

    const titleEl = document.getElementById("modal-detail-title") || document.getElementById("modal-title");
    if(titleEl) titleEl.innerText = movie.title;
    
    const descEl = document.getElementById("modal-detail-desc") || document.getElementById("modal-desc");
    if(descEl) descEl.innerText = movie.overview || "Overview is currently unavailable for this movie.";

    const episodesSection = document.getElementById('series-episodes-section');
    
    if (isSeriesMovie) {
        if(episodesSection) episodesSection.style.display = 'block';
        const seasonSelect = document.getElementById('season-select');
        if(seasonSelect) {
            seasonSelect.dataset.movieId = movieId;
            seasonSelect.value = "1"; 
        }
        loadEpisodes(movieId, 1); 
    } else {
        if(episodesSection) episodesSection.style.display = 'none';
    }

    // 🛑 ĐÂY LÀ CHỖ ĐƯỢC SỬA: Lấy trực tiếp độ tuổi từ Backend/SQL Server (biến movie)
    const ratingEl = document.getElementById("modal-rating");
    if (ratingEl) {
        ratingEl.innerText = movie.age_rating || movie.AgeRating || "T16";
    }

try {
        const tmdbType = isSeriesMovie ? 'tv' : 'movie';
        
        // 🛑 TRẢ VỀ BẢN TIẾNG ANH (language=en-US)
        const res = await fetch(`https://api.themoviedb.org/3/${tmdbType}/${movieId}?api_key=${TMDB_API_KEY}&language=en-US&append_to_response=credits`);
        const data = await res.json();
        
        // 🛑 TUYỆT CHIÊU BÙ ĐẮP DATA (Bản Tiếng Anh)
        if (!movie.overview || movie.overview === "null" || movie.overview.trim() === "") {
            const descEl = document.getElementById("modal-detail-desc") || document.getElementById("modal-desc");
            if (descEl) {
                // Nếu SQL trống -> Lấy overview Tiếng Anh của TMDB đắp vào.
                descEl.innerText = data.overview || "Overview is currently unavailable for this movie.";
            }
        }
        if (isSeriesMovie && data.number_of_seasons) {
            const seasonSelect = document.getElementById('season-select');
            if (seasonSelect) {
                seasonSelect.innerHTML = ''; // Xóa sạch 2 cái option mùa 1, mùa 2 bị fix cứng ở HTML
                
                // Vòng lặp: Phim có bao nhiêu mùa thì đẻ ra bấy nhiêu thẻ option
                for (let i = 1; i <= data.number_of_seasons; i++) {
                    const opt = document.createElement('option');
                    opt.value = i;
                    opt.innerText = `Season ${i}`;
                    seasonSelect.appendChild(opt);
                }
                // Đặt mặc định lúc vừa mở Popup lên là Mùa 1
                seasonSelect.value = "1"; 
            }
        }
        
        if(document.getElementById("modal-hero") && data.backdrop_path) {
            document.getElementById("modal-hero").style.backgroundImage = `url('https://image.tmdb.org/t/p/original${data.backdrop_path}')`;
        }
        if(document.getElementById("modal-cast") && data.credits && data.credits.cast) {
            document.getElementById("modal-cast").innerText = data.credits.cast.slice(0, 5).map(c => c.name).join(", ");
        }
        if(document.getElementById("modal-genres") && data.genres) {
            document.getElementById("modal-genres").innerText = data.genres.map(g => g.name).join(", ");
        }
        if(document.getElementById("modal-duration")) {
            let runtime = data.runtime || (data.episode_run_time && data.episode_run_time[0]) || 0;
            document.getElementById("modal-duration").innerText = runtime > 0 ? `${Math.floor(runtime/60)}h ${runtime%60}m` : "HD";
        }
        
        if (document.getElementById("modal-year")) {
            let dateString = data.release_date || data.first_air_date || "";
            document.getElementById("modal-year").innerText = dateString ? dateString.substring(0, 4) : "N/A";
        }
        
        // (Đã xóa trắng cái cục logic if...else dài ngoằng dùng để giải mã rating của TMDB ở đây)

    } catch (e) { console.error("Error fetching TMDB details:", e); }

    const likeBtn = document.getElementById("modal-like-btn");
    if(likeBtn) {
        likeBtn.onclick = async () => {
            try {
                const res = await fetch(`${API_BASE}/favorites`, {
                    method: "POST", headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ profile_id: parseInt(activeProfileId), movie_id: movieId })
                });
                const result = await res.json();
                if(result.status === "added") {
                    likeBtn.style.background = "rgba(70, 211, 105, 0.3)";
                    likeBtn.style.borderColor = "#46d369";
                } else {
                    likeBtn.style.background = "rgba(42,42,42,0.6)";
                    likeBtn.style.borderColor = "rgba(255,255,255,0.5)";
                }
            } catch(e) {}
        };
    }

    const addBtn = document.getElementById("modal-add-btn") || document.getElementById("fav-btn");
    if(addBtn) {
        addBtn.onclick = () => addToWatchlist(movieId);
    }

    fetch(`${API_BASE}/history`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile_id: parseInt(activeProfileId), movie_id: movieId })
    }).catch(e => {});
    
    loadRecommendations(movieId);
}

function closeModal() {
    const modal = document.getElementById("movieModal");
    if(modal) modal.style.display = "none";
    document.body.style.overflow = "auto";
    loadWatchHistory();
}

// ==========================================
// 5. TÌM KIẾM & K-MEANS
// ==========================================
async function loadRecommendations(movieId) {
    const list = document.getElementById("recommend-list");
    if(!list) return;
    list.innerHTML = "<p style='color: white;'>🤖 AI is analyzing data...</p>";
    try {
        const res = await fetch(`${API_BASE}/recommend/${movieId}`);
        const data = await res.json();
        list.innerHTML = "";
        data.recommendations.forEach(m => list.appendChild(createMovieCard(m)));
    } catch (e) { 
        list.innerHTML = "<p style='color:red;'>AI has not clustered this movie yet.</p>"; 
    }
}


async function searchMovies() {
    const q = document.getElementById("searchInput").value.trim();
    if(!q) return clearSearch();
    
    if(document.getElementById("hero-banner")) document.getElementById("hero-banner").style.display = "none";
    document.querySelectorAll(".tab-container").forEach(c => c.style.display = "none");
    
    document.getElementById("search-container").style.display = "block";
    if(document.getElementById("search-keyword")) document.getElementById("search-keyword").innerText = q;
    
    const list = document.getElementById("search-results-list");
    if(list) {
        list.innerHTML = "<p style='color: white;'>⏳ Searching...</p>";
        try {
            const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(q)}`);
            const movies = await res.json();
            list.innerHTML = movies.length ? "" : "<p style='color: #E50914;'>❌ No movies found.</p>";
            movies.forEach(m => list.appendChild(createMovieCard(m)));
        } catch (e) { list.innerHTML = "<p style='color: red;'>Server error!</p>"; }
    }
}

function clearSearch() {
    if(document.getElementById("searchInput")) document.getElementById("searchInput").value = "";
    if(document.getElementById("search-container")) document.getElementById("search-container").style.display = "none";
    if(document.getElementById("hero-banner")) document.getElementById("hero-banner").style.display = "flex"; 
    
    const activeTab = document.querySelector('.nav-links li a.active');
    if (activeTab) {
        activeTab.click();
    } else {
        if(document.getElementById("tab-home")) document.getElementById("tab-home").style.display = "block";
    }
}

// ==========================================
// HỆ THỐNG ĐA SERVER
// ==========================================
const SERVERS = [
    { 
        name: "MultiEmbed (Most stable)", 
        getMovie: (id) => `https://multiembed.mov/?video_id=${id}&tmdb=1&autoplay=1`, 
        getTv: (id, s, e) => `https://multiembed.mov/?video_id=${id}&tmdb=1&s=${s}&e=${e}&autoplay=1` 
    },
    { 
        name: "VidLink", 
        getMovie: (id) => `https://vidlink.pro/movie/${id}?autoplay=1`, 
        getTv: (id, s, e) => `https://vidlink.pro/tv/${id}/${s}/${e}?autoplay=1` 
    },
    { 
        name: "VidSrc", 
        getMovie: (id) => `https://vidsrc.net/embed/movie?tmdb=${id}`, 
        getTv: (id, s, e) => `https://vidsrc.net/embed/tv?tmdb=${id}&season=${s}&episode=${e}` 
    },
    { 
        name: "2Embed", 
        getMovie: (id) => `https://www.2embed.cc/embed/${id}`, 
        getTv: (id, s, e) => `https://www.2embed.cc/embed/tv/${id}/${s}/${e}` 
    }
];

function renderServerButtons(movieId, type = 'movie', season = 1, episode = 1) {
    const videoFrame = document.getElementById('videoFrame');
    if (!videoFrame) return;

    videoFrame.setAttribute("allowfullscreen", "true");
    videoFrame.setAttribute("webkitallowfullscreen", "true");
    videoFrame.setAttribute("mozallowfullscreen", "true");
    
    videoFrame.style.marginTop = "15px"; 
    videoFrame.style.height = "75vh"; 
    videoFrame.style.display = "block";
    videoFrame.style.boxSizing = "border-box";
    videoFrame.style.border = "none";

    let container = document.getElementById('server-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'server-container';
        container.style.cssText = "text-align: center; margin-bottom: 5px; padding: 5px; margin-top: -30px;";
        videoFrame.parentNode.insertBefore(container, videoFrame); 
    }

    container.innerHTML = '<span style="color: #fff; margin-right: 15px; font-weight: bold;">Choose Server (Switch if error):</span>';

    SERVERS.forEach((server) => {
        let btn = document.createElement('button');
        btn.innerText = server.name;
        btn.style.cssText = "margin: 0 5px; padding: 8px 15px; cursor: pointer; background: #333; color: white; border: 1px solid #555; border-radius: 4px; font-weight: bold; transition: 0.3s;";
        
        btn.onclick = () => {
            videoFrame.src = type === 'movie' ? server.getMovie(movieId) : server.getTv(movieId, season, episode);
            Array.from(container.querySelectorAll('button')).forEach(b => b.style.background = '#333');
            btn.style.background = '#e50914'; 
        };
        
        container.appendChild(btn);
    });

    container.querySelectorAll('button')[0].click();
}

// ==========================================
// HÀM PHÁT PHIM LẺ
// ==========================================
async function playMovie(youtubeUrl, movieId) {
    if (!movieId) {
        alert("Movie ID not found to play!");
        return;
    }

    fetch(`${API_BASE}/history`, {
        method: "POST", 
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile_id: parseInt(activeProfileId), movie_id: movieId })
    }).catch(e => console.error("Error saving history:", e));

    const videoModal = document.getElementById('videoModal');
    if (videoModal) {
        videoModal.style.display = 'flex';
        renderServerButtons(movieId, 'movie');
    }
}

// ==========================================
// HÀM PHÁT PHIM BỘ
// ==========================================
function playSeriesEpisode(movieId, season, episode) {
    const videoModal = document.getElementById('videoModal');
    if (videoModal) {
        videoModal.style.display = 'flex';
        renderServerButtons(movieId, 'tv', season, episode);
    }
}

// --- Hàm đóng Video ---
function closeVideo() {
    const videoModal = document.getElementById('videoModal');
    const videoFrame = document.getElementById('videoFrame');
    if (videoModal) {
        videoModal.style.display = 'none';
    }
    if (videoFrame) {
        videoFrame.src = ""; 
    }
}

// ==========================================
// 7. HÀM CHUYỂN ĐỔI GIAO DIỆN (ĐÃ NÂNG CẤP LƯU TRẠNG THÁI)
// ==========================================
function switchTab(tabName, element) {
    // 1. Cập nhật nút nào đang sáng (active) trên thanh Navbar
    const links = document.querySelectorAll(".nav-links li a");
    links.forEach(link => link.classList.remove("active"));
    
    if (element) {
        element.classList.add("active");
    } else {
        // Nếu hệ thống tự gọi lúc F5 thì tự đi tìm nút để làm sáng lên
        const targetLink = document.querySelector(`.nav-links li a[onclick*="${tabName}"]`);
        if (targetLink) targetLink.classList.add("active");
    }

    // 2. Chuyển đổi nội dung bên dưới (Tự động giấu hết tab-container)
    const containers = document.querySelectorAll(".tab-container");
    containers.forEach(c => c.style.display = "none");

    const activeTarget = document.getElementById(`tab-${tabName}`);
    if (activeTarget) {
        activeTarget.style.display = "block";
    }

    // 3. Tắt/Bật Hero Banner
    const heroBanner = document.getElementById("hero-banner");
    if (heroBanner) {
        if (["home", "series", "movies", "new-popular"].includes(tabName)) {
            heroBanner.style.display = "flex";
            
            // 🛑 GỌI LỆNH ĐỔI BỘ PHIM TRÊN BANNER THEO TAB
            if (tabName === "series") loadHeroBanner("tv");
            else if (tabName === "movies") loadHeroBanner("movie");
            else loadHeroBanner("popular"); 
            
        } else {
            heroBanner.style.display = "none";
        }
    }
    
    // ==========================================
    // 4. KÍCH HOẠT DỮ LIỆU CHO BROWSE BY LANGUAGES
    // ==========================================
    if (tabName === "languages") {
        if (typeof loadLanguageMovies === "function") {
            loadLanguageMovies();
        }
    }
    
    localStorage.setItem("currentSmartFlixTab", tabName);
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ==========================================
// 8. TẢI DANH SÁCH TẬP PHIM
// ==========================================
async function loadEpisodes(movieId, seasonNumber) {
    const episodesList = document.getElementById('episodes-list');
    if(!episodesList) return;
    episodesList.innerHTML = '<p style="color: #999;">⏳ Loading episode data...</p>';

    try {
        // 🛑 Lấy chi tiết tập phim bằng API tiếng Anh
        const res = await fetch(`https://api.themoviedb.org/3/tv/${movieId}/season/${seasonNumber}?api_key=${TMDB_API_KEY}&language=en-US`);
        const data = await res.json();

        if (!data.episodes || data.episodes.length === 0) {
            episodesList.innerHTML = '<p style="color: #999;">No episode data available for this season.</p>';
            return;
        }

        episodesList.innerHTML = '';
        data.episodes.forEach(ep => {
            const row = document.createElement('div');
            row.style.cssText = "display: flex; align-items: center; padding: 15px; border-bottom: 1px solid #333; cursor: pointer; transition: background 0.2s; border-radius: 4px;";
            row.onmouseover = () => row.style.backgroundColor = "#333";
            row.onmouseout = () => row.style.backgroundColor = "transparent";
            
            row.onclick = () => playSeriesEpisode(movieId, seasonNumber, ep.episode_number);

            const imgUrl = ep.still_path ? `https://image.tmdb.org/t/p/w300${ep.still_path}` : 'backgrnetflix.jpg';
            
            const overview = ep.overview ? ep.overview : "Overview is currently unavailable for this episode.";
            const runtime = ep.runtime ? `${ep.runtime}m` : '';

            row.innerHTML = `
                <div style="font-size: 24px; color: #d2d2d2; width: 40px; text-align: center; font-weight: bold;">${ep.episode_number}</div>
                <div style="width: 140px; min-width: 140px; margin-right: 15px; border-radius: 4px; overflow: hidden;">
                    <img src="${imgUrl}" alt="${ep.name}" style="width: 100%; height: auto; display: block; object-fit: cover;">
                </div>
                <div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: center;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                        <h4 style="margin: 0; font-size: 16px; color: #fff;">Episode ${ep.episode_number}: ${ep.name}</h4>
                        <span style="color: #d2d2d2; font-size: 14px; font-weight: 500;">${runtime}</span>
                    </div>
                    <p style="margin: 0; font-size: 13px; color: #bcbcbc; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">
                        ${overview}
                    </p>
                </div>
            `;
            episodesList.appendChild(row);
        });
    } catch (e) {
        episodesList.innerHTML = '<p style="color: red;">❌ Server connection error for TV shows!</p>';
    }
}

function changeSeason(seasonNumber) {
    const movieId = document.getElementById('season-select').dataset.movieId;
    if (movieId) loadEpisodes(movieId, seasonNumber);
}

// ==========================================
// HÀM LỌC PHIM THEO THỂ LOẠI TỪ DROP-DOWN
// ==========================================
async function filterMoviesByGenre(genreId) {
    const defaultContent = document.getElementById("default-movies-content");
    const filteredContent = document.getElementById("filtered-movies-content");

    if (genreId === "all") {
        defaultContent.style.display = "block";  
        filteredContent.style.display = "none";  
        return;
    }

    defaultContent.style.display = "none";    
    filteredContent.style.display = "grid";   
    
    filteredContent.innerHTML = "<p style='color: white; font-size: 18px; grid-column: 1 / -1; text-align: center; margin-top: 40px;'>⏳ Filtering films by genre...</p>";

    try {
        const res = await fetch(`${API_BASE}/movies/genre/${genreId}`);
        const movies = await res.json();
        
        filteredContent.innerHTML = ""; 
        
        if(movies.length === 0) {
            filteredContent.innerHTML = "<p style='color: gray; font-size: 16px; grid-column: 1 / -1; text-align: center;'>No films available for this genre yet.</p>";
        } else {
            movies.forEach(m => filteredContent.appendChild(createMovieCard(m)));
        }
    } catch (e) { 
        console.error(e);
        filteredContent.innerHTML = "<p style='color: #e50914; font-size: 16px; grid-column: 1 / -1; text-align: center;'>❌ Server connection error!</p>"; 
    }
}

// ==========================================
// HÀM LỌC SERIES THEO THỂ LOẠI TỪ DROP-DOWN
// ==========================================
async function filterSeriesByGenre(genreId) {
    const defaultContent = document.getElementById("default-series-content");
    const filteredContent = document.getElementById("filtered-series-content");

    if (genreId === "all") {
        defaultContent.style.display = "block";
        filteredContent.style.display = "none";
        return;
    }

    defaultContent.style.display = "none";
    filteredContent.style.display = "grid";
    
    filteredContent.innerHTML = "<p style='color: white; font-size: 18px; grid-column: 1 / -1; text-align: center; margin-top: 40px;'>⏳ Filtering series by genre...</p>";

    try {
        const res = await fetch(`${API_BASE}/series/genre/${genreId}`);
        const series = await res.json();
        
        filteredContent.innerHTML = ""; 
        
        if(series.length === 0) {
            filteredContent.innerHTML = "<p style='color: gray; font-size: 16px; grid-column: 1 / -1; text-align: center;'>No series available for this genre yet.</p>";
        } else {
            series.forEach(m => filteredContent.appendChild(createMovieCard(m)));
        }
    } catch (e) { 
        console.error("Error filtering series:", e);
        filteredContent.innerHTML = "<p style='color: #e50914; font-size: 16px; grid-column: 1 / -1; text-align: center;'>❌ Server connection error!</p>"; 
    }
}
// ==========================================
// HIỆU ỨNG TÌM KIẾM CHUẨN NETFLIX
// ==========================================
function toggleSearch() {
    const searchBox = document.querySelector('.search-box');
    const searchInput = document.getElementById('searchInput');
    
    if (searchBox.classList.contains('active') && searchInput.value.trim() !== "") {
        searchMovies(); 
        return; 
    }

    searchBox.classList.toggle('active');
    
    if(searchBox.classList.contains('active')) {
        searchInput.focus(); 
    } else {
        searchInput.value = ''; 
    }
}

// ==========================================
// TẠO THẺ TOP 10 VÀ TẢI TRANG NEW & POPULAR
// ==========================================
function createTop10Card(movie, index) {
    const div = document.createElement("div");
    div.className = "top10-card";
    
    div.innerHTML = `
        <div class="top10-number">${index + 1}</div>
        <div class="top10-img-wrapper">
            <img src="${movie.poster}" alt="${movie.title}" title="${movie.title}">
            <div class="top10-badge">TOP<br>10</div>
        </div>
    `;
    
    // Bấm vào thẻ Top 10 thì vẫn mở popup chi tiết phim bình thường
    div.onclick = () => openMovieDetail(movie);
    return div;
}

async function loadNewAndPopular() {
    try {
        // 1. Tăng limit lên 100 để gọi vét được nhiều phim nhất có thể
        const res = await fetch(`${API_BASE}/movies?limit=100`); 
        const allMovies = await res.json();
        
        const topMovies = allMovies.filter(m => m.IsSeries == 0 || m.IsSeries === "0" || m.IsSeries === false || m.IsSeries === null).slice(0, 10);

        const topSeries = allMovies.filter(m => m.IsSeries == 1 || m.IsSeries === "1" || m.IsSeries === true).slice(0, 10);
                // ==========================================
        // 🛑 BÍ KÍP XỬ LÝ MẢNG "BẤT TỬ" CHO NEW ADDED & WORTH WAIT
        // ==========================================
        // Xáo trộn ngẫu nhiên mảng để mỗi lần tải lại trang là phim hiện ra khác nhau
        let shuffled = [...allMovies].sort(() => 0.5 - Math.random());

        // Cắt dữ liệu thông minh: 
        // Lấy 15 phim đầu cho "New Added"
        const newAdded = shuffled.slice(0, 15);
        
        // Bọc lót: Nếu kho phim có hơn 15 bộ -> Lấy 15 bộ tiếp theo cho "Worth Wait"
        // Nếu kho phim quá ít (dưới 15 bộ) -> Lấy luôn mảng ban đầu đắp vào để không bao giờ bị trống hàng!
        const worthWait = shuffled.length > 15 ? shuffled.slice(15, 30) : shuffled.slice(0, 15);
        
        // Đổ danh sách Phim Mới
        const newAddedList = document.getElementById("new-added-list");
        if (newAddedList) {
            newAddedList.innerHTML = "";
            newAdded.forEach(m => newAddedList.appendChild(createMovieCard(m)));
        }
        
        // Đổ danh sách Đáng Mong Đợi
        const worthWaitList = document.getElementById("worth-wait-list");
        if (worthWaitList) {
            worthWaitList.innerHTML = "";
            worthWait.forEach(m => worthWaitList.appendChild(createMovieCard(m)));
        }

        // Đổ danh sách TOP 10 Series
        const top10SeriesList = document.getElementById("top10-series-list");
        if (top10SeriesList) {
            top10SeriesList.innerHTML = "";
            topSeries.forEach((m, i) => top10SeriesList.appendChild(createTop10Card(m, i)));
        }

        // Đổ danh sách TOP 10 Phim lẻ
        const top10MoviesList = document.getElementById("top10-movies-list");
        if (top10MoviesList) {
            top10MoviesList.innerHTML = "";
            topMovies.forEach((m, i) => top10MoviesList.appendChild(createTop10Card(m, i)));
        }

        // ĐỔ VÀO TRANG CHỦ HOME 
        const homeTop10Series = document.getElementById("home-top10-series");
        if (homeTop10Series) {
            homeTop10Series.innerHTML = "";
            topSeries.forEach((m, i) => homeTop10Series.appendChild(createTop10Card(m, i)));
        }

        const homeTop10Movies = document.getElementById("home-top10-movies");
        if (homeTop10Movies) {
            homeTop10Movies.innerHTML = "";
            topMovies.forEach((m, i) => homeTop10Movies.appendChild(createTop10Card(m, i)));
        }

    } catch (e) { console.error("Error loading New & Popular:", e); }
}

// ==========================================
// HÀM TẢI PHIM CHO TRANG BROWSE BY LANGUAGES (ĐÃ ĐỒNG BỘ 100%)
// ==========================================
async function loadLanguageMovies() {
    const grid = document.getElementById("language-movies-grid");
    const langSelect = document.getElementById("lang-select");
    
    if (!grid) return; 

    async function fetchAndRender(languageValue) {
        try {
            grid.innerHTML = "<h3 style='grid-column: 1 / -1; color: #a3a3a3; text-align: center;'>Loading movies...</h3>";
            
            const res = await fetch(`${API_BASE}/movies/language/${languageValue}`); 
            if (!res.ok) throw new Error("API failed");
            let movies = await res.json();

            grid.innerHTML = ""; 

            if (movies.length === 0) {
                grid.innerHTML = "<h3 style='grid-column: 1 / -1; color: #a3a3a3; text-align: center; margin-top: 50px;'>No movies found for this language.</h3>";
                return;
            }

            // TÁI SỬ DỤNG KHUÔN ĐÚC CỦA ÔNG
            movies.forEach(movie => {
                const card = createMovieCard(movie);
                grid.appendChild(card);
            });
        } catch (e) {
            console.error("Lỗi tải phim ngôn ngữ:", e);
            grid.innerHTML = "<h3 style='grid-column: 1 / -1; color: red; text-align: center;'>Error loading movies. Please check backend API.</h3>";
        }
    }

    if (langSelect) {
        fetchAndRender(langSelect.value);
        langSelect.onchange = (e) => fetchAndRender(e.target.value);
    }
}

// ==========================================
// KHỞI CHẠY TẤT CẢ KHI MỞ TRANG
// ==========================================
window.onload = () => {

    

    loadMovies();
    loadWatchHistory();
    loadWatchlist();
    loadFavoriteMovies();
    loadNewAndPopular();

    loadMoviesByGenre(28, "home-top-picks");       
    loadMoviesByGenre(10749, "home-romance-list"); 
    loadMoviesByGenre(53, "home-thriller-list");   
    loadMoviesByGenre(35, "home-comedy-list");     
    loadMoviesByGenre(878, "home-scifi-list");     
    loadMoviesByGenre(10751, "home-family-list");  
    loadMoviesByGenre(12, "home-adventure-list");  
    loadMoviesByGenre(9648, "home-mystery-list");  
    loadMoviesByGenre(14, "home-fantasy-list");    
    loadMoviesByGenre(36, "home-history-list");    
    loadMoviesByGenre(10402, "home-music-list");   
    
    loadMoviesByGenre(28, "action-list");          
    loadMoviesByGenre(27, "horror-list");          
    loadMoviesByGenre(35, "movie-comedy-list");    
    loadMoviesByGenre(878, "movie-scifi-list");    
    loadMoviesByGenre(53, "movie-thriller-list");  


    loadSeriesByGenre(16, "animation-list");       
    loadSeriesByGenre(80, "series-crime-list");    
    loadSeriesByGenre(9648, "series-mystery-list");
    loadSeriesByGenre(18, "series-drama-list");    
    loadSeriesByGenre(35, "series-comedy-list");   
    loadSeriesByGenre(10765, "series-scifi-list");


    const savedTab = localStorage.getItem("currentSmartFlixTab");
    if (savedTab) {
        // Nếu có trí nhớ -> Mở lại tab trước lúc bị F5
        switchTab(savedTab, null);
    } else {
        // Nếu mới đăng nhập vào lần đầu -> Mặc định mở trang Home
        switchTab('home', null);
    }
}; 
