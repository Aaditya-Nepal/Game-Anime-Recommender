const API_BASE = 'http://localhost:5000/api';

// Global state
const appState = {
  currentTab: 'anime',
  searchQuery: '',
  popularAnime: [],
  popularGames: [],
  searchResults: [],
  loading: false,
  error: null,
  cache: new Map(),
};

// DOM refs
const refs = {
  tabs: document.querySelectorAll('.tab'),
  animeSection: document.getElementById('popular-anime'),
  gameSection: document.getElementById('popular-game'),
  animeGrid: document.getElementById('animeGrid'),
  gameGrid: document.getElementById('gameGrid'),
  resultsGrid: document.getElementById('resultsGrid'),
  searchInput: document.getElementById('searchInput'),
  clearSearch: document.getElementById('clearSearch'),
  modal: document.getElementById('modal'),
  modalTitle: document.getElementById('modalTitle'),
  modalBadges: document.getElementById('modalBadges'),
  modalMeta: document.getElementById('modalMeta'),
  modalImage: document.getElementById('modalImage'),
  recGrid: document.getElementById('recommendationsGrid'),
  viewRecs: document.getElementById('viewRecommendations'),
  year: document.getElementById('year'),
  toasts: document.getElementById('toasts'),
};

// Utils
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const saveHistory = (q) => {
  if (!q) return;
  const key = 'mdr.search';
  const now = Date.now();
  const hist = JSON.parse(localStorage.getItem(key) || '[]').filter(x => typeof x === 'object');
  const filtered = hist.filter(x => x.query.toLowerCase() !== q.toLowerCase());
  filtered.unshift({ query: q, at: now });
  localStorage.setItem(key, JSON.stringify(filtered.slice(0, 10)));
};
const loadHistory = () => JSON.parse(localStorage.getItem('mdr.search') || '[]');
const toast = (msg) => {
  const el = document.createElement('div');
  el.className = 'toast';
  el.textContent = msg;
  refs.toasts.appendChild(el);
  setTimeout(() => el.remove(), 3000);
};

// Networking with caching and error handling
async function apiGet(path) {
  const url = `${API_BASE}${path}`;
  if (appState.cache.has(url)) return appState.cache.get(url);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  const data = await res.json();
  appState.cache.set(url, data);
  return data;
}

async function apiPost(path, body) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

// Required functions
async function fetchPopularAnime(force = false) {
  try {
    setLoading(true, refs.animeGrid);
    if (!force && appState.popularAnime.length) return appState.popularAnime;
    const { success, data } = await apiGet('/anime/popular');
    if (success) {
      appState.popularAnime = data;
      renderCards(data, refs.animeGrid, 'anime');
      return data;
    }
  } catch (e) { handleError(e); }
  finally { setLoading(false, refs.animeGrid); }
}

async function fetchPopularGames(force = false) {
  try {
    setLoading(true, refs.gameGrid);
    if (!force && appState.popularGames.length) return appState.popularGames;
    const { success, data } = await apiGet('/games/popular');
    if (success) {
      appState.popularGames = data;
      renderCards(data, refs.gameGrid, 'game');
      return data;
    }
  } catch (e) { handleError(e); }
  finally { setLoading(false, refs.gameGrid); }
}

async function searchContent(query) {
  try {
    if (!query || query.trim().length === 0) { 
      // Show popular sections again and clear search results
      showPopularSections();
      refs.resultsGrid.innerHTML = ''; 
      return []; 
    }
    
    appState.searchQuery = query;
    setLoading(true, refs.resultsGrid);
    
    // Hide popular sections and show search results
    hidePopularSections();
    showSearchResults();
    
    // Search for the current tab type only (anime OR games, not both)
    const currentType = appState.currentTab;
    let results = [];
    
    try {
      // Get results for current type only (limit to 12)
      const response = await apiPost('/search-recommendations', { query, type: currentType, limit: 12 });
      if (response.success && response.data) {
        results = response.data.slice(0, 12); // Ensure max 12
      }
    } catch (e) {
      console.warn('Search recommendations failed, falling back to simple search:', e);
      
      // Fallback to simple search
      try {
        if (currentType === 'anime') {
          const animeSearch = await apiGet(`/anime/search/${encodeURIComponent(query)}`);
          if (animeSearch.success && animeSearch.data) {
            results = animeSearch.data.slice(0, 12); // Limit to 12
          }
        } else {
          const gameSearch = await apiGet(`/games/search/${encodeURIComponent(query)}`);
          if (gameSearch.success && gameSearch.data) {
            results = gameSearch.data.slice(0, 12); // Limit to 12
          }
        }
      } catch (fallbackError) {
        console.error('Fallback search also failed:', fallbackError);
      }
    }
    
    // Ensure all results have the correct type
    results = results.map(item => ({ ...item, type: currentType }));
    
    appState.searchResults = results;
    
    // Render results in the search results grid
    renderCards(results, refs.resultsGrid);
    saveHistory(query);
    
    return results;
  } catch (e) { 
    handleError(e); 
    return [];
  } finally { 
    setLoading(false, refs.resultsGrid); 
  }
}

async function getRecommendations(title, type, limit = 25) {
  try {
    setLoading(true, refs.recGrid);
    const { success, data } = await apiPost('/recommend', { title, type, limit });
    if (success) {
      renderCards(data, refs.recGrid, type);
      return data;
    }
  } catch (e) { handleError(e); }
  finally { setLoading(false, refs.recGrid); }
}

// Rendering
function renderCards(items, container, kind) {
  container.innerHTML = '';
  const frag = document.createDocumentFragment();
  for (const item of items) {
    frag.appendChild(createCard(item, kind));
  }
  container.appendChild(frag);
}

function createCard(item, overrideType) {
  const type = overrideType || item.type || 'anime';
  const card = document.createElement('article');
  card.className = `card ${type === 'game' ? 'game' : 'anime'}`;
  card.tabIndex = 0;
  card.setAttribute('role', 'button');
  card.dataset.title = item.title;
  card.dataset.type = type;

  const imgUrl = item.image_url || placeholderFor(type);
  const rating = Number(item.rating || 0).toFixed(1);
  const genre = (item.metadata && item.metadata.genre) ? item.metadata.genre : '';
  const year = (item.metadata && item.metadata.year) ? item.metadata.year : '';
  const price = (item.metadata && item.metadata.price) ? item.metadata.price : null;

  card.innerHTML = `
    <div class="thumb">
      <img loading="lazy" src="${imgUrl}" alt="${item.title}">
    </div>
    <div class="content">
      <h3 class="title">${item.title}</h3>
      <div class="meta">
        <span class="rating">★ ${rating}</span>
        ${genre ? `<span class="badge">${escapeHtml(genre)}</span>` : ''}
        ${year ? `<span>${year}</span>` : ''}
        ${price ? `<span class="badge warn">${price}</span>` : ''}
      </div>
    </div>
  `;

  // Harden image: replace with placeholder on error
  const imgEl = card.querySelector('img');
  imgEl.addEventListener('error', () => { imgEl.src = placeholderFor(type); });

  // Clamp long titles visually to avoid overflow issues
  const titleEl = card.querySelector('.title');
  titleEl.style.display = 'box';
  titleEl.style.webkitLineClamp = '2';
  titleEl.style.webkitBoxOrient = 'vertical';
  titleEl.style.overflow = 'hidden';

  card.addEventListener('click', () => openModal(item));
  card.addEventListener('keydown', (e) => { if (e.key === 'Enter') openModal(item); });
  return card;
}

function renderSuggestions(query, items) {
  refs.suggestions.innerHTML = '';
  const q = query.trim().toLowerCase();
  const unique = [];
  const seen = new Set();
  for (const it of items) {
    const t = it.title;
    if (seen.has(t)) continue;
    if (t.toLowerCase().includes(q)) { unique.push(t); seen.add(t); }
    if (unique.length >= 6) break;
  }
  const hist = loadHistory().map(x => x.query).filter(x => !seen.has(x));
  for (const s of [...unique, ...hist].slice(0, 10)) {
    const div = document.createElement('div');
    div.className = 'item';
    div.role = 'option';
    div.textContent = s;
    div.addEventListener('click', () => { refs.searchInput.value = s; handleSearch(); });
    refs.suggestions.appendChild(div);
  }
}

// Modal logic
let currentModalItem = null;
function openModal(item){
  currentModalItem = item;
  refs.modalTitle.textContent = item.title;
  refs.modalBadges.innerHTML = '';
  if (item.metadata && item.metadata.genre) {
    const b = document.createElement('span'); b.className = 'badge'; b.textContent = item.metadata.genre; refs.modalBadges.appendChild(b);
  }
  refs.modalMeta.textContent = `${item.metadata?.year ? item.metadata.year + ' • ' : ''}Rating: ${Number(item.rating||0).toFixed(1)}`;
  refs.modalImage.innerHTML = `<img src="${item.image_url || placeholderFor(item.type)}" alt="${item.title}">`;
  refs.recGrid.innerHTML = '';
  refs.modal.setAttribute('aria-hidden', 'false');
}
function closeModal(){ refs.modal.setAttribute('aria-hidden', 'true'); refs.recGrid.innerHTML=''; currentModalItem=null; }

// Loading helpers
function setLoading(isLoading, container){
  container?.setAttribute('aria-busy', isLoading ? 'true' : 'false');
  if (isLoading) {
    container.innerHTML = '';
    const t = document.getElementById('card-skeleton');
    for (let i=0;i<8;i++){ container.appendChild(t.content.cloneNode(true)); }
  }
}
function handleError(e){ console.error(e); toast('Something went wrong. Please try again.'); }

// Debounce
function debounce(fn, wait){ let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn.apply(null, args), wait); }; }

// Events
const debouncedSearch = debounce(() => handleSearch(), 300);
function handleSearch(){ 
  const q = refs.searchInput.value.trim(); 
  if (q) {
    searchContent(q);
  } else {
    // If search is empty, show popular sections and clear results
    showPopularSections();
    refs.resultsGrid.innerHTML = '';
  }
}

function switchTabs(tab){
  appState.currentTab = tab;
  const animeActive = tab === 'anime';
  refs.animeSection.classList.toggle('hidden', !animeActive);
  refs.gameSection.classList.toggle('hidden', animeActive);
  for (const b of refs.tabs){ b.classList.toggle('active', b.dataset.tab === tab); b.setAttribute('aria-selected', String(b.dataset.tab === tab)); }
}

// Clear search function
function clearSearch() {
  refs.searchInput.value = '';
  refs.resultsGrid.innerHTML = '';
  showPopularSections();
  // Scroll back to top
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Placeholder images
function placeholderFor(type){
  const grad = type === 'game'
    ? 'linear-gradient(135deg, #2196F3, #FF6B35)'
    : 'linear-gradient(135deg, #4CAF50, #2196F3)';
  // Tiny SVG data URI for performance
  const svg = encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' width='600' height='900'><defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0%' stop-color='${type==='game'?'#2196F3':'#4CAF50'}'/><stop offset='100%' stop-color='${type==='game'?'#FF6B35':'#2196F3'}'/></linearGradient></defs><rect width='100%' height='100%' fill='url(#g)'/><text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' fill='rgba(0,0,0,0.4)' font-size='36' font-family='Segoe UI, Roboto'>${type==='game'?'GAME':'ANIME'}</text></svg>`);
  return `data:image/svg+xml;charset=utf-8,${svg}`;
}

function escapeHtml(s){ return s?.replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])) || ''; }

// Infinite scroll (load more suggestions from search results)
let observer;
function setupInfiniteScroll(){
  if (observer) observer.disconnect();
  observer = new IntersectionObserver(entries => {
    for (const e of entries){
      if (e.isIntersecting && appState.searchResults.length){
        // For demo, just re-render to simulate pagination (no backend pagination provided)
        renderCards(appState.searchResults, refs.resultsGrid);
      }
    }
  });
  const sentinel = document.createElement('div');
  sentinel.style.height = '1px';
  refs.resultsGrid.appendChild(sentinel);
  observer.observe(sentinel);
}

// Touch: swipe between tabs
function setupSwipe(){
  let startX = 0; let dx = 0; const onStart = (e)=>{ startX = (e.touches?e.touches[0].clientX:e.clientX); };
  const onMove = (e)=>{ dx = (e.touches?e.touches[0].clientX:e.clientX) - startX; };
  const onEnd = ()=>{ if (Math.abs(dx) > 80){ switchTabs(dx > 0 ? 'anime' : 'game'); } startX = 0; dx = 0; };
  document.addEventListener('touchstart', onStart, { passive: true });
  document.addEventListener('touchmove', onMove, { passive: true });
  document.addEventListener('touchend', onEnd);
}

// Function to hide popular sections
function hidePopularSections() {
  if (refs.animeSection) refs.animeSection.style.display = 'none';
  if (refs.gameSection) refs.gameSection.style.display = 'none';
}

// Function to show popular sections
function showPopularSections() {
  if (refs.animeSection) refs.animeSection.style.display = 'block';
  if (refs.gameSection) refs.gameSection.style.display = 'block';
}

// Function to show search results section
function showSearchResults() {
  const searchResultsSection = document.querySelector('.results');
  if (searchResultsSection) {
    searchResultsSection.style.display = 'block';
    // Scroll to search results
    searchResultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// Function to clear search results and show popular sections
function clearSearchResults() {
  refs.resultsGrid.innerHTML = '';
  showPopularSections();
  // Scroll back to top
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Init
function init(){
  refs.year.textContent = new Date().getFullYear();
  refs.tabs.forEach(b => b.addEventListener('click', () => switchTabs(b.dataset.tab)));
  refs.clearSearch.addEventListener('click', clearSearch);
  
  // Add event listener for clear results button
  const clearResultsBtn = document.getElementById('clearResults');
  if (clearResultsBtn) {
    clearResultsBtn.addEventListener('click', clearSearchResults);
  }
  
  refs.searchInput.addEventListener('input', debouncedSearch);
  refs.searchInput.addEventListener('keydown', (e)=>{ if(e.key==='Enter'){ e.preventDefault(); handleSearch(); } if(e.key==='Escape'){ refs.searchInput.blur(); }});
  document.querySelectorAll('[data-refresh]').forEach(btn => btn.addEventListener('click', ()=>{
    const t = btn.getAttribute('data-refresh');
    if (t === 'anime') fetchPopularAnime(true); else fetchPopularGames(true);
  }));
  document.querySelectorAll('[data-close="modal"]').forEach(el => el.addEventListener('click', closeModal));
  refs.viewRecs.addEventListener('click', async ()=>{ if (!currentModalItem) return; await getRecommendations(currentModalItem.title, currentModalItem.type || appState.currentTab, 12); });

  // Menu button toggles tabs on mobile
  const menu = document.querySelector('.menu-toggle');
  const nav = document.getElementById('primary-nav');
  menu.addEventListener('click', ()=>{ const exp = nav.style.display === 'flex'; nav.style.display = exp ? 'none' : 'flex'; menu.setAttribute('aria-expanded', String(!exp)); });

  // Prefetch
  fetchPopularAnime();
  fetchPopularGames();
  setupInfiniteScroll();
  setupSwipe();
}

document.addEventListener('DOMContentLoaded', init);


