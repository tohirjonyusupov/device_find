# DeviceGuard — Deploy Qo'llanmasi

## Arxitektura
- **Backend**: Railway (FastAPI)
- **Database**: Supabase (PostgreSQL)
- **Frontend**: Vercel (HTML/JS)

---

## 1. Supabase — Database

1. https://supabase.com ga kiring → "New project" yarating
2. **Settings → Database → Connection string → URI** bo'limidan URL oling
3. URL ni quyidagicha o'zgartiring:
   ```
   postgresql://postgres.[ref]:[parol]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```
   → asyncpg uchun:
   ```
   postgresql+asyncpg://postgres.[ref]:[parol]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```

---

## 2. Railway — Backend

1. https://railway.app ga kiring
2. **"New Project" → "Deploy from GitHub repo"** → bu reponi tanlang
3. **Variables** bo'limida quyidagilarni qo'shing:

| Variable | Qiymat |
|---|---|
| `DATABASE_URL` | Supabase connection string (asyncpg) |
| `SECRET_KEY` | Kamida 32 ta belgi (masalan: `openssl rand -hex 32`) |
| `FRONTEND_URL` | Vercel URL (keyinroq qo'shiladi) |

4. Deploy tugagach, Railway sizga URL beradi: `https://xxx.railway.app`

---

## 3. Vercel — Frontend

1. https://vercel.com ga kiring
2. **"Add New Project" → GitHub repo** → `frontend` papkasini **Root Directory** qilib belgilang
3. Deploy tugagach URL oling: `https://xxx.vercel.app`
4. Bu URLni Railway da `FRONTEND_URL` ga qo'shing

---

## 4. Frontend — API URL ni yangilang

`frontend/js/app.js` faylida va barcha HTML fayllardagi:
```js
const API = 'http://localhost:8000';
```
ni Railway URL ga o'zgartiring:
```js
const API = 'https://xxx.railway.app';
```

**Yoki Vercel environment variable ishlatish:**

Vercel da `VITE_API_URL` o'rniga har bir HTML faylda `window.API_BASE` ni o'rnating.

**Tezkor usul** — barcha HTML fayllarni o'zgartirish:
```bash
find frontend -name "*.html" -exec sed -i 's|http://localhost:8000|https://YOUR-RAILWAY-URL.railway.app|g' {} \;
```

---

## 5. Admin yaratish

Backend birinchi marta ishga tushganda admin avtomatik yaratiladi:
- Email: `admin@deviceguard.com`
- Parol: `Admin1234!`

**Muhim:** Ishga tushgandan so'ng parolni o'zgartiring!

---

## Lokal ishga tushirish

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (yangi terminal)
cd frontend
python -m http.server 5500
```

Sahifalar:
- Frontend: http://localhost:5500
- API Docs: http://localhost:8000/docs
- Admin: http://localhost:5500/admin-login.html
