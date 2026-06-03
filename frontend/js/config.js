// ── DeviceGuard API Configuration ──────────────────────────
// Local ishlatganda: http://localhost:8000
// Production da: Railway URL

const API = (function() {
  const host = window.location.hostname;
  if (host === 'localhost' || host === '127.0.0.1') {
    return 'http://localhost:8000';
  }
  // Production: Railway backend URL (deploy qilgandan keyin o'zgartiriladi)
  return 'https://device-find.onrender.com';
})();
