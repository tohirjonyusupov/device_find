// ── DeviceGuard Global App JS ──────────────────────────────────────────────
// API is defined in each HTML page's inline script

// ── AUTH ──
function getToken() { return localStorage.getItem('dg_token'); }
function getUser()  { try { return JSON.parse(localStorage.getItem('dg_user') || '{}'); } catch { return {}; } }
function authHeaders() {
  return { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' };
}
function requireAuth() {
  if (!getToken()) { window.location.href = authRedirectPath() + 'login.html'; return false; }
  return true;
}
function authRedirectPath() {
  const p = window.location.pathname;
  return p.includes('/dashboard/') ? '../' : p.endsWith('/') ? '' : './';
}
function logout() {
  localStorage.removeItem('dg_token');
  localStorage.removeItem('dg_user');
  window.location.href = authRedirectPath() + 'login.html';
}

// ── THEME ──
const THEME_KEY = 'dg_theme';
function getTheme() { return localStorage.getItem(THEME_KEY) || 'dark'; }
function applyTheme(theme) {
  const isLight = theme === 'light';
  document.documentElement.setAttribute('data-theme', theme);
  document.documentElement.classList.toggle('light-mode', isLight);
  // body may be null if called before DOM is ready (from <head>)
  if (document.body) {
    document.body.setAttribute('data-theme', theme);
    document.body.classList.toggle('light-mode', isLight);
  }
  localStorage.setItem(THEME_KEY, theme);
  // Update theme icon buttons
  document.querySelectorAll('[data-theme-icon]').forEach(el => {
    el.innerHTML = isLight
      ? '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>'
      : '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';
  });
}
function toggleTheme() { applyTheme(getTheme() === 'dark' ? 'light' : 'dark'); }

// ── LANGUAGE ──
const LANG_KEY = 'dg_lang';
function getLang() { return localStorage.getItem(LANG_KEY) || 'uz'; }
function setLang(l) { localStorage.setItem(LANG_KEY, l); applyTranslations(); updateNavbar(); }

const T = {
  uz: {
    // Nav
    dashboard: "Qurilmalarim", subscription: "Obuna", profile: "Profil",
    admin: "Admin", logout: "Chiqish", search_public: "Qidiruv",
    // Auth
    loginBtn: "Kirish", regBtn: "Ro'yxat",
    // Device
    addDevice: "Qurilma qo'shish", noDevices: "Qurilmalar yo'q hali",
    active: "Faol", lost: "Yo'qolgan", found: "Topilgan",
    phone: "Telefon", laptop: "Noutbuk", tablet: "Planshet",
    watch: "Soat", headphones: "Quloqchin", camera: "Kamera", other: "Boshqa",
    updateStatus: "Holatni o'zgartirish", edit: "Tahrirlash", delete: "O'chirish",
    save: "Saqlash", cancel: "Bekor qilish",
    // Subscription
    freePlan: "Bepul", proPlan: "PRO", upgradeBtn: "PRO ga o'tish",
    devices: "qurilma",
    // Status
    loading: "Yuklanmoqda...",
  },
  en: {
    dashboard: "My Devices", subscription: "Subscription", profile: "Profile",
    admin: "Admin", logout: "Logout", search_public: "Search",
    loginBtn: "Login", regBtn: "Register",
    addDevice: "Add Device", noDevices: "No devices yet",
    active: "Active", lost: "Lost", found: "Found",
    phone: "Phone", laptop: "Laptop", tablet: "Tablet",
    watch: "Watch", headphones: "Headphones", camera: "Camera", other: "Other",
    updateStatus: "Update Status", edit: "Edit", delete: "Delete",
    save: "Save", cancel: "Cancel",
    freePlan: "Free", proPlan: "PRO", upgradeBtn: "Upgrade to PRO",
    devices: "devices",
    loading: "Loading...",
  },
  ru: {
    dashboard: "Устройства", subscription: "Подписка", profile: "Профиль",
    admin: "Админ", logout: "Выйти", search_public: "Поиск",
    loginBtn: "Войти", regBtn: "Регистрация",
    addDevice: "Добавить", noDevices: "Нет устройств",
    active: "Активно", lost: "Потеряно", found: "Найдено",
    phone: "Телефон", laptop: "Ноутбук", tablet: "Планшет",
    watch: "Часы", headphones: "Наушники", camera: "Камера", other: "Другое",
    updateStatus: "Изменить статус", edit: "Изменить", delete: "Удалить",
    save: "Сохранить", cancel: "Отмена",
    freePlan: "Бесплатно", proPlan: "PRO", upgradeBtn: "Перейти на PRO",
    devices: "устройств",
    loading: "Загрузка...",
  }
};

function t(key) { return T[getLang()]?.[key] || T.en[key] || key; }

function applyTranslations() {
  // text content — supports both data-t (legacy) and data-i18n
  document.querySelectorAll('[data-t], [data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n') || el.getAttribute('data-t');
    const val = t(key);
    if (val) el.textContent = val;
  });
  // placeholder
  document.querySelectorAll('[data-t-placeholder], [data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder') || el.getAttribute('data-t-placeholder');
    const val = t(key);
    if (val) el.placeholder = val;
  });
  // aria-label
  document.querySelectorAll('[data-i18n-aria]').forEach(el => {
    const val = t(el.getAttribute('data-i18n-aria'));
    if (val) el.setAttribute('aria-label', val);
  });
  // title attribute
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const val = t(el.getAttribute('data-i18n-title'));
    if (val) el.title = val;
  });
}

// ── NAVBAR ──
function buildNavbar(opts = {}) {
  const lang = getLang();
  const prefix = opts.prefix || '';
  const hasToken = !!getToken();
  const user = getUser();

  const langBtns = ['uz','en','ru'].map(l =>
    `<button onclick="setLang('${l}')" data-lang-btn="${l}" class="px-2.5 py-1 text-xs rounded-lg font-medium transition">${l.toUpperCase()}</button>`
  ).join('');

  return `
<nav id="mainNav" class="dg-nav border-b px-4 py-3 sticky top-0 backdrop-blur z-50">
  <div class="max-w-6xl mx-auto flex items-center justify-between">
    <a href="${prefix}index.html" class="flex items-center gap-2 font-bold">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>
      <span class="hidden sm:inline">DeviceGuard</span>
    </a>
    <div class="flex items-center gap-1.5">
      <a href="${prefix}lost-devices.html" class="hidden sm:flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-xl dg-btn-ghost text-red-400 hover:bg-red-900/20 transition">
        <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
        Yo'qolganlar
      </a>
      <div class="flex gap-0.5 p-1 rounded-xl dg-lang-wrap">${langBtns}</div>
      <button onclick="toggleTheme()" data-theme-icon class="p-2 rounded-xl dg-btn-ghost"></button>
      ${hasToken ? `
        <a href="${prefix}dashboard/index.html" class="p-2 rounded-xl dg-btn-ghost hidden sm:flex" title="${t('dashboard')}">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
        </a>
        <a href="${prefix}dashboard/subscription.html" class="p-2 rounded-xl dg-btn-ghost hidden sm:flex" title="${t('subscription')}">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
        </a>
        <a href="${prefix}dashboard/chat.html" class="p-2 rounded-xl dg-btn-ghost hidden sm:flex relative" title="Chat">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <span id="chatUnreadBadge" class="hidden absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 rounded-full text-xs flex items-center justify-center font-bold"></span>
        </a>
        <a href="${prefix}dashboard/profile.html" class="p-2 rounded-xl dg-btn-ghost hidden sm:flex" title="${t('profile')}">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        </a>
        ${user.role==='admin' ? `<a href="${prefix}dashboard/admin.html" class="p-2 rounded-xl text-red-400 hover:bg-red-900/20" title="Admin"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 1.41 1.41"/></svg></a>` : ''}
        <button onclick="logout()" class="p-2 rounded-xl dg-btn-ghost text-red-400" title="${t('logout')}">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
        </button>
      ` : `
        <a href="${prefix}login.html" class="px-3 py-1.5 text-sm font-medium dg-btn-ghost rounded-xl" data-t="loginBtn">${t('loginBtn')}</a>
        <a href="${prefix}register.html" class="px-3 py-1.5 text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition" data-t="regBtn">${t('regBtn')}</a>
      `}
    </div>
  </div>
</nav>`;
}

function updateNavbar() {
  // Update lang buttons active state
  const lang = getLang();
  document.querySelectorAll('[data-lang-btn]').forEach(btn => {
    const l = btn.getAttribute('data-lang-btn');
    if (l === lang) {
      btn.classList.add('bg-blue-600','text-white');
      btn.classList.remove('dg-lang-inactive');
    } else {
      btn.classList.remove('bg-blue-600','text-white');
      btn.classList.add('dg-lang-inactive');
    }
  });
  // Update data-t elements in nav
  applyTranslations();
}

// ── THEME CSS (injected once) ──
function injectThemeStyles() {
  if (document.getElementById('dg-theme-styles')) return;
  const style = document.createElement('style');
  style.id = 'dg-theme-styles';
  style.textContent = `
/* ── CSS VARIABLES ── */
:root {
  --dg-bg:         #030712;
  --dg-surface:    #111827;
  --dg-surface2:   #1f2937;
  --dg-surface3:   #374151;
  --dg-border:     #374151;
  --dg-text:       #f9fafb;
  --dg-text2:      #d1d5db;
  --dg-text3:      #9ca3af;
  --dg-text4:      #6b7280;
  --dg-input-bg:   #1f2937;
  --dg-nav-bg:     rgba(3,7,18,0.95);
}
[data-theme="light"] {
  --dg-bg:         #f8fafc;
  --dg-surface:    #ffffff;
  --dg-surface2:   #f1f5f9;
  --dg-surface3:   #e2e8f0;
  --dg-border:     #e2e8f0;
  --dg-text:       #0f172a;
  --dg-text2:      #1e293b;
  --dg-text3:      #475569;
  --dg-text4:      #94a3b8;
  --dg-input-bg:   #ffffff;
  --dg-nav-bg:     rgba(248,250,252,0.97);
}

/* ── BASE ── */
body { background-color: var(--dg-bg); color: var(--dg-text); min-height: 100vh; transition: background 0.2s, color 0.2s; }

/* ── NAVBAR ── */
.dg-nav { background: var(--dg-nav-bg); border-color: var(--dg-border); color: var(--dg-text); }
.dg-nav a, .dg-nav button { color: var(--dg-text3); }
.dg-nav a:hover { color: var(--dg-text); }
.dg-nav .font-bold { color: var(--dg-text) !important; }
.dg-btn-ghost { transition: background 0.15s; }
.dg-btn-ghost:hover { background: var(--dg-surface2); }
.dg-lang-wrap { background: var(--dg-surface); border: 1px solid var(--dg-border); }
.dg-lang-inactive { color: var(--dg-text3); }
.dg-lang-inactive:hover { background: var(--dg-surface2); color: var(--dg-text); }

/* ── BACKGROUNDS ── */
.bg-gray-950  { background-color: var(--dg-bg)       !important; }
.bg-gray-900  { background-color: var(--dg-surface)  !important; }
.bg-gray-800  { background-color: var(--dg-surface2) !important; }
.bg-gray-700  { background-color: var(--dg-surface3) !important; }
.bg-gray-600  { background-color: var(--dg-surface3) !important; }
[class*="bg-gray-800\\/"] { background-color: var(--dg-surface2) !important; }
[class*="bg-gray-900\\/"] { background-color: var(--dg-surface)  !important; }

/* ── BORDERS ── */
.border-gray-800, .border-gray-700, .border-gray-600 { border-color: var(--dg-border) !important; }
[class*="divide-gray-"] > * + * { border-color: var(--dg-border) !important; }
[class*="ring-gray-"]   { --tw-ring-color: var(--dg-border) !important; }

/* ── TEXT ── */
.text-white   { color: var(--dg-text)  !important; }
.text-gray-100, .text-gray-200 { color: var(--dg-text2) !important; }
.text-gray-300 { color: var(--dg-text2) !important; }
.text-gray-400, .text-gray-500 { color: var(--dg-text3) !important; }
.text-gray-600 { color: var(--dg-text4) !important; }

/* ── INPUTS ── */
input, select, textarea {
  background-color: var(--dg-input-bg) !important;
  border-color: var(--dg-border) !important;
  color: var(--dg-text) !important;
}
input::placeholder, textarea::placeholder { color: var(--dg-text4) !important; }
input:focus, select:focus, textarea:focus {
  border-color: #3b82f6 !important;
  outline: none !important;
  box-shadow: 0 0 0 2px rgba(59,130,246,0.2) !important;
}
select option {
  background-color: var(--dg-surface) !important;
  color: var(--dg-text) !important;
}

/* ── CARDS / MODALS ── */
.bg-black\\/70, .bg-black\\/80 { background-color: rgba(0,0,0,0.55) !important; }
[data-theme="light"] .bg-black\\/70,
[data-theme="light"] .bg-black\\/80 { background-color: rgba(0,0,0,0.35) !important; }

/* ── BADGES ── */
[data-theme="light"] .bg-green-900\\/30  { background-color: rgba(187,247,208,0.6) !important; }
[data-theme="light"] .bg-red-900\\/30    { background-color: rgba(254,202,202,0.6) !important; }
[data-theme="light"] .bg-yellow-900\\/30 { background-color: rgba(254,240,138,0.6) !important; }
[data-theme="light"] .bg-blue-900\\/30   { background-color: rgba(191,219,254,0.6) !important; }
[data-theme="light"] .text-green-400  { color: #16a34a !important; }
[data-theme="light"] .text-red-400    { color: #dc2626 !important; }
[data-theme="light"] .text-yellow-400 { color: #ca8a04 !important; }
[data-theme="light"] .text-blue-400   { color: #2563eb !important; }
[data-theme="light"] .border-green-800 { border-color: #bbf7d0 !important; }
[data-theme="light"] .border-red-800   { border-color: #fecaca !important; }
[data-theme="light"] .border-yellow-800 { border-color: #fef08a !important; }

/* ── GRADIENTS ── */
.from-blue-900\\/50 { --tw-gradient-from: rgba(30,58,138,0.15) !important; }
.from-blue-900\\/40 { --tw-gradient-from: rgba(30,58,138,0.12) !important; }
.to-gray-900 { --tw-gradient-to: var(--dg-surface) !important; }
[data-theme="light"] .from-blue-900\\/50 { --tw-gradient-from: rgba(219,234,254,0.8) !important; }
[data-theme="light"] .from-blue-900\\/40 { --tw-gradient-from: rgba(219,234,254,0.6) !important; }
[data-theme="light"] .to-gray-900 { --tw-gradient-to: #ffffff !important; }

/* ── HOVER STATES IN LIGHT MODE ── */
[data-theme="light"] .hover\\:bg-gray-800:hover { background-color: var(--dg-surface2) !important; }
[data-theme="light"] .hover\\:bg-gray-700:hover { background-color: var(--dg-surface3) !important; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--dg-bg); }
::-webkit-scrollbar-thumb { background: var(--dg-border); border-radius: 3px; }
  `;
  document.head.appendChild(style);
}

// ── INIT — runs immediately when app.js loads ──
injectThemeStyles();
applyTheme(getTheme());

document.addEventListener('DOMContentLoaded', () => {
  // Apply theme to body now that DOM is ready
  const theme = getTheme();
  document.body.setAttribute('data-theme', theme);
  document.body.classList.toggle('light-mode', theme === 'light');

  // Build navbar from data-prefix attribute if inline script didn't do it
  const navEl = document.getElementById('navbar');
  if (navEl && !navEl.innerHTML.trim()) {
    const prefix = navEl.getAttribute('data-prefix') || '';
    navEl.innerHTML = buildNavbar({ prefix });
  }
  updateNavbar();
  applyTranslations();
  if (window.lucide) lucide.createIcons();

  // Chat unread badge (agar login bo'lgan bo'lsa)
  if (getToken()) {
    async function refreshUnread() {
      try {
        const res = await fetch(`${API}/chat/unread-count`, { headers: authHeaders() });
        if (!res.ok) return;
        const { count } = await res.json();
        const badge = document.getElementById('chatUnreadBadge');
        if (badge) {
          badge.textContent = count > 9 ? '9+' : count;
          badge.classList.toggle('hidden', count === 0);
        }
      } catch {}
    }
    refreshUnread();
    setInterval(refreshUnread, 15000);
  }
});
