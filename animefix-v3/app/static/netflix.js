let animeData = [];
let currentIndex = -1;
let currentHls = null;
let lastFocusedElement = null;

// Storage for playback progress
const PROGRESS_KEY = 'anime_playback_progress';

document.addEventListener('DOMContentLoaded', () => {
    fetchAnimes();
    fetchRecentEpisodes();
    
    // Navbar scroll effect
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            document.getElementById('navbar').classList.add('scrolled');
        } else {
            document.getElementById('navbar').classList.remove('scrolled');
        }
    });

    document.getElementById('closeModalBtn').addEventListener('click', closeModal);
    document.getElementById('closePlayerBtn').addEventListener('click', closePlayer);

    // D-PAD Navigation Support
    document.addEventListener('keydown', handleKeyDown);

    // Video Progress Tracking
    const video = document.getElementById('videoPlayer');
    video.addEventListener('timeupdate', () => {
        if (video.dataset.epId && video.currentTime > 5) {
            saveProgress(video.dataset.epId, video.currentTime, video.duration);
        }
    });

    // --- TV EXCLUSIVE MODE ---
    // If the native Android TV app is loading this site, strip everything except the logo and new episodes.
    if (navigator.userAgent.includes("AnimeFixTV")) {
        applyTVExclusiveLayout();
    }
});

function applyTVExclusiveLayout() {
    window.isTVExclusiveMode = true;

    // Remove Navbar entirely
    const navbar = document.getElementById('navbar');
    if (navbar) navbar.style.display = 'none';

    // Hide Hero Section
    const hero = document.getElementById('hero');
    if (hero) hero.style.display = 'none';
    
    // Hide The "All Animes" row
    const animeGridRow = document.getElementById('animeGrid')?.closest('.row');
    if (animeGridRow) animeGridRow.style.display = 'none';

    // Ensure the New Episodes row acts as the top of the page
    const newEpsRow = document.getElementById('newEpisodesGrid')?.closest('.row');
    if (newEpsRow) newEpsRow.style.marginTop = '20px'; // Less margin since there's no navbar
}

function handleKeyDown(e) {    const focusable = Array.from(document.querySelectorAll('[tabindex], button, video'));
    let current = document.activeElement;
    
    if (e.key === 'Enter') {
        if (current.onclick) current.onclick();
        else if (current.tagName === 'BUTTON') current.click();
        return;
    }

    // Modal close handling
    if (e.key === 'Escape' || e.key === 'Back' || e.key === 'Backspace') {
        if (document.getElementById('playerPanel').style.display === 'block') {
            closePlayer();
            e.preventDefault();
        } else if (document.getElementById('detailsModal').style.display === 'flex') {
            closeModal();
            e.preventDefault();
        }
        return;
    }
}

// TV Spatial Navigation - Auto Scroll to focused element
document.addEventListener('focus', function(e) {
    if (e.target && e.target.scrollIntoView) {
        // Only scroll if it's a card, episode, or button
        if (e.target.classList.contains('anime-card') || 
            e.target.classList.contains('ep-item') ||
            e.target.tagName === 'BUTTON' ||
            e.target.tagName === 'A') {
            
            // Use block: center to keep it in the middle of the TV screen
            e.target.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
        }
    }
}, true);

async function fetchAnimes() {
    try {
        const res = await fetch('/api/animes');
        animeData = await res.json();
        renderHome();
        setupHero();
    } catch (err) {
        console.error("Error fetching animes:", err);
    }
}

function renderHome() {
    renderAnimesGrid(animeData, 'animeGrid');
    
    // Recently Added (Sort by ID or Sync Date)
    const recent = [...animeData].sort((a,b) => b.id - a.id).slice(0, 10);
    renderAnimesGrid(recent, 'recentGrid');

    // Continue Watching
    renderContinueWatching();
}

async function fetchRecentEpisodes() {
    try {
        console.log("Fetching recent episodes...");
        const res = await fetch('/api/episodes/recent');
        const eps = await res.json();
        console.log("Recent episodes found:", eps.length);
        renderRecentEpisodes(eps);
    } catch (err) {
        console.error("Error fetching recent episodes:", err);
    }
}

function renderRecentEpisodes(eps) {
    const grid = document.getElementById('newEpisodesGrid');
    const row = grid.closest('.row');
    
    if (eps.length === 0) {
        row.style.display = 'none'; // Hide if empty to not frustrate user
        return;
    }
    
    row.style.display = 'block';
    grid.innerHTML = '';
    eps.forEach(ep => {
        const card = document.createElement('div');
        card.className = 'anime-card';
        card.tabIndex = 0;
        card.innerHTML = `
            <img src="${ep.thumb_url || 'https://via.placeholder.com/300x450?text=Ep'}" alt="${ep.title}">
            <div class="anime-info">
                <div class="anime-name">${ep.anime_name}</div>
                <div style="font-size:0.75rem; color:var(--netflix-red); font-weight:bold;">Novo: Ep ${ep.number}</div>
            </div>
        `;
        // Find media type from animeData if possible, or assume m3u8 for recent
        // Direct play: clicking card opens player
        card.onclick = () => {
             console.log("Playing recent episode:", ep.id, ep.media_type);
             playEpisode(ep.id, ep.anime_name, ep.number, ep.media_type);
        };
        grid.appendChild(card);
    });

    // Auto-focus the first element if in TV mode
    if (window.isTVExclusiveMode) {
        setTimeout(() => {
            const firstCard = grid.querySelector('.anime-card');
            if (firstCard) firstCard.focus();
        }, 100);
    }
}

function renderAnimesGrid(data, containerId) {
    const grid = document.getElementById(containerId);
    grid.innerHTML = '';
    data.forEach(anime => {
        const card = document.createElement('div');
        card.className = 'anime-card';
        card.tabIndex = 0;
        card.innerHTML = `
            <img src="${anime.poster_url || 'https://via.placeholder.com/300x450?text=No+Poster'}" alt="${anime.name}">
            <div class="anime-info">
                <div class="anime-name">${anime.name}</div>
                <div style="font-size:0.7rem; color:var(--text-muted)">${anime.episodes.length} episódios</div>
            </div>
        `;
        card.onclick = () => showDetails(anime);
        grid.appendChild(card);
    });
}

function renderContinueWatching() {
    if (window.isTVExclusiveMode) {
        document.getElementById('continueWatchingRow').style.display = 'none';
        return;
    }
    const progress = JSON.parse(localStorage.getItem(PROGRESS_KEY) || '{}');
    const row = document.getElementById('continueWatchingRow');
    const grid = document.getElementById('continueGrid');
    grid.innerHTML = '';

    const items = Object.values(progress).sort((a,b) => b.timestamp - a.timestamp);
    
    if (items.length > 0) {
        row.style.display = 'block';
        items.forEach(item => {
            // Find episode in animeData
            let ep = null;
            let targetAnime = null;
            for(const a of animeData) {
                ep = a.episodes.find(e => e.id == item.epId);
                if(ep) { targetAnime = a; break; }
            }

            if(ep) {
                const card = document.createElement('div');
                card.className = 'anime-card';
                card.tabIndex = 0;
                const percent = (item.time / item.duration) * 100;
                
                card.innerHTML = `
                    <img src="${targetAnime.poster_url}" alt="${targetAnime.name}">
                    <div style="position:absolute; bottom:0; left:0; width:100%; height:4px; background:#444;">
                        <div style="width:${percent}%; height:100%; background:var(--netflix-red);"></div>
                    </div>
                    <div class="anime-info">
                        <div class="anime-name">${targetAnime.name}</div>
                        <div style="font-size:0.7rem;">Episódio ${ep.number}</div>
                    </div>
                `;
                card.onclick = () => playEpisode(ep.id, targetAnime.name, ep.number, ep.media_type, item.time);
                grid.appendChild(card);
            }
        });
    } else {
        row.style.display = 'none';
    }
}

function setupHero() {
    if (animeData.length === 0) return;
    const hero = animeData[Math.floor(Math.random() * animeData.length)];
    if (hero.poster_url) {
        document.getElementById('hero').style.backgroundImage = `url('${hero.poster_url}')`;
    }
    document.getElementById('heroTitle').textContent = hero.name;
    document.getElementById('heroSynopsis').textContent = hero.description || "Nenhuma descrição disponível.";
    
    // Setup MAL link
    // Setup MAL link (Always show, use search as fallback)
    const malBtn = document.getElementById('heroMalLink');
    if (hero.mal_url) {
        malBtn.href = hero.mal_url;
    } else {
        // Fallback to MyAnimeList search
        malBtn.href = `https://myanimelist.net/anime.php?q=${encodeURIComponent(hero.name)}`;
    }
    malBtn.style.display = 'flex';
    
    currentIndex = animeData.indexOf(hero);
}

function showDetails(anime) {
    lastFocusedElement = document.activeElement;
    const modal = document.getElementById('detailsModal');
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    document.getElementById('modalAnimeTitle').textContent = anime.name;
    document.getElementById('modalHeaderBanner').style.backgroundImage = `url('${anime.poster_url}')`;
    
    // Meta Info
    const addedDate = new Date(anime.last_sync_date).toLocaleDateString('pt-BR');
    document.getElementById('modalAnimeMeta').textContent = `Adicionado em: ${addedDate} • ${anime.episodes.length} episódios`;
    document.getElementById('modalAnimeSynopsis').textContent = anime.description || "Nenhuma sinopse disponível.";

    const seasonGroups = document.getElementById('seasonGroups');
    seasonGroups.innerHTML = '';

    const seasons = {};
    anime.episodes.forEach(ep => {
        if (!seasons[ep.season]) seasons[ep.season] = [];
        seasons[ep.season].push(ep);
    });

    const sortedSeasons = Object.keys(seasons).sort((a,b) => a - b);
    sortedSeasons.forEach(s => {
        const group = document.createElement('div');
        group.className = 'season-group';
        group.innerHTML = `<h3 class="season-title">Temporada ${s}</h3>`;
        const epList = document.createElement('div');
        epList.className = 'ep-list';
        
        seasons[s].sort((a,b) => parseFloat(a.number) - parseFloat(b.number)).forEach(ep => {
            const item = document.createElement('div');
            item.className = 'ep-item';
            item.tabIndex = 0;
            const canPlay = ep.status === 'Online' || ep.status === 'Pending' || ep.status === 'Renovating';

            item.innerHTML = `
                <div class="ep-thumb">
                    ${ep.thumb_url ? `<img src="${ep.thumb_url}" style="width:100%;height:100%;object-fit:cover">` : '<i class="ph ph-image-square" style="font-size:2rem; opacity:0.3"></i>'}
                </div>
                <div class="ep-info">
                    <div class="ep-num">Episódio ${ep.number} ${ep.title ? '- ' + ep.title : ''}</div>
                    <div style="font-size: 0.8rem; color: #aaa; margin: 4px 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                        ${ep.description || 'Sem descrição.'}
                    </div>
                    <div class="ep-status">${ep.status}</div>
                </div>
                ${canPlay ? '<i class="ph ph-play-fill" style="font-size:1.5rem"></i>' : ''}
            `;
            if (canPlay) item.onclick = () => playEpisode(ep.id, anime.name, ep.number, ep.media_type);
            epList.appendChild(item);
        });
        group.appendChild(epList);
        seasonGroups.appendChild(group);
    });

    // Focus first ep item
    const firstEp = seasonGroups.querySelector('.ep-item');
    if (firstEp) firstEp.focus();
}

function playEpisode(epId, animeName, epNumber, mediaType, resumeTime = 0) {
    const lastFocus = document.activeElement;
    const panel = document.getElementById('playerPanel');
    panel.style.display = 'block';
    
    const video = document.getElementById('videoPlayer');
    video.dataset.epId = epId;
    video.tabIndex = 0;
    
    const streamUrl = `/stream/${epId}`;
    if (currentHls) currentHls.destroy();

    if (mediaType === 'youtube' || mediaType === 'iframe') {
        const container = document.getElementById('videoContainer');
        const existingIframe = container.querySelector('iframe');
        if (existingIframe) existingIframe.remove();
        video.style.display = 'none';
        const iframe = document.createElement('iframe');
        iframe.src = streamUrl;
        iframe.referrerPolicy = "no-referrer";
        iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
        iframe.allowFullscreen = true;
        container.appendChild(iframe);
        iframe.focus();
    } else {
        video.style.display = 'block';
        if (Hls.isSupported()) {
            currentHls = new Hls();
            currentHls.loadSource(streamUrl);
            currentHls.attachMedia(video);
            currentHls.on(Hls.Events.MANIFEST_PARSED, () => {
                if (resumeTime > 0) video.currentTime = resumeTime;
                video.play();
            });
        } else {
            video.src = streamUrl;
            video.oncanplay = () => {
                if (resumeTime > 0) video.currentTime = resumeTime;
                video.play();
            };
        }
        video.focus();
    }
}

function saveProgress(epId, time, duration) {
    const progress = JSON.parse(localStorage.getItem(PROGRESS_KEY) || '{}');
    progress[epId] = {
        epId,
        time,
        duration,
        timestamp: Date.now()
    };
    // Keep only last 20 items
    const keys = Object.keys(progress).sort((a,b) => progress[b].timestamp - progress[a].timestamp);
    if(keys.length > 20) {
        keys.slice(20).forEach(k => delete progress[k]);
    }
    localStorage.setItem(PROGRESS_KEY, JSON.stringify(progress));
}

function closeModal() {
    document.getElementById('detailsModal').style.display = 'none';
    document.body.style.overflow = 'auto';
    if (lastFocusedElement) lastFocusedElement.focus();
}

function closePlayer() {
    document.getElementById('playerPanel').style.display = 'none';
    const video = document.getElementById('videoPlayer');
    video.pause();
    if (currentHls) {
        currentHls.destroy();
        currentHls = null;
    }
    renderContinueWatching();
    if (lastFocusedElement) lastFocusedElement.focus();
}

function playRandom() {
    if (currentIndex !== -1) showDetails(animeData[currentIndex]);
}
