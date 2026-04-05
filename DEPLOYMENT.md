# SPECTRA-AI Deployment Guide

## Architecture

```
┌─────────────────────┐     ┌──────────────────────┐     ┌──────────────┐
│   spectra.html      │────▶│  FastAPI Backend      │────▶│  Supabase    │
│   (any static host) │     │  (Render.com / VPS)   │     │  (already ✅)│
└─────────────────────┘     └──────────────────────┘     └──────────────┘
```

- **Frontend** (`spectra.html`) — static HTML, host anywhere (Netlify, GitHub Pages, or just open locally)
- **Backend** (`api/main1.py`) — FastAPI, needs a server with ~2GB RAM for ML models
- **Database** — Supabase (already deployed and running ✅)
- **Model file** — `efficientnet_b0_spectra.pth` — upload separately (too large for Git)

---

## Option A: Render.com (Recommended — Free tier available)

### Step 1: Push to GitHub

```bash
# In your project folder
git init
git add .
git commit -m "SPECTRA-AI initial deploy"
git remote add origin https://github.com/YOUR_USERNAME/spectra-ai.git
git push -u origin main
```

> ⚠️ Make sure `.gitignore` excludes `.env` and model files — they're already in it.

### Step 2: Create Render Web Service

1. Go to [render.com](https://render.com) → **New → Web Service**
2. Connect your GitHub repo
3. Render will auto-detect the `render.yaml` file
4. Set these **Environment Variables** in the Render dashboard:
   - `SUPABASE_KEY` → your Supabase service role key (from Supabase → Settings → API)
   - `NEWS_API_KEY` → your NewsAPI key
   - `GNEWS_API_KEY` → your GNews key
   - `GOOGLE_API_KEY` → your Google API key

### Step 3: Upload your model file

Since `efficientnet_b0_spectra.pth` is too large for Git, upload it to the Render persistent disk:

```bash
# After first deploy, use Render Shell (dashboard → Shell tab)
# OR use scp if you have SSH access:
scp efficientnet_b0_spectra.pth user@your-render-instance:/data/efficientnet_b0_spectra.pth
```

**Alternative:** Upload model to Supabase Storage or Google Drive and download on startup:
```python
# Add to startup_event() in main1.py
import urllib.request
if not os.path.exists('/data/efficientnet_b0_spectra.pth'):
    print("Downloading model...")
    urllib.request.urlretrieve('YOUR_MODEL_PUBLIC_URL', '/data/efficientnet_b0_spectra.pth')
```

### Step 4: Update spectra.html

After Render deploys, you'll get a URL like `https://spectra-api.onrender.com`.

Open `spectra.html`, find this line near the top of the `<script>` section:
```js
const DEPLOYED_API_URL = '';
```
Change it to:
```js
const DEPLOYED_API_URL = 'https://spectra-api.onrender.com';
```

### Step 5: Host the frontend

**Option 1 — Netlify (easiest):**
1. Go to [netlify.com](https://netlify.com) → **Add new site → Deploy manually**
2. Drag and drop just the `spectra.html` file
3. Done — you'll get a URL like `https://spectra-xyz.netlify.app`

**Option 2 — GitHub Pages:**
```bash
# In a separate repo or gh-pages branch
cp spectra.html index.html
git add index.html && git commit -m "deploy frontend"
git push
# Enable GitHub Pages in repo Settings → Pages
```

**Option 3 — Serve from FastAPI (simplest):**
Add to `api/main1.py`:
```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

@app.get("/")
async def serve_frontend():
    return FileResponse("spectra.html")
```
Then your entire app is at `https://spectra-api.onrender.com`

---

## Option B: Railway.app (Alternative)

1. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub**
2. Select your repo
3. Railway auto-detects Docker
4. Add environment variables in the Railway dashboard
5. For the model file: use Railway's Volume feature (similar to Render disk)

---

## Option C: Local Docker (for testing)

```bash
# 1. Build image
docker build -t spectra-ai .

# 2. Place your model file in the project folder
cp /path/to/efficientnet_b0_spectra.pth ./

# 3. Copy env template
cp .env.production .env
# Edit .env with your real keys

# 4. Start
docker-compose up

# API is now at http://localhost:8000
# Open spectra.html in browser
```

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | ✅ | Your Supabase project URL |
| `SUPABASE_KEY` | ✅ | Supabase **service role** key (not anon key — needs write access) |
| `NEWS_API_KEY` | ✅ | [newsapi.org](https://newsapi.org) free key |
| `GNEWS_API_KEY` | ⚡ Optional | [gnews.io](https://gnews.io) key |
| `GOOGLE_API_KEY` | ⚡ Optional | For Google Custom Search |
| `GOOGLE_CX` | ⚡ Optional | Google Custom Search Engine ID |
| `DEVICE` | ✅ | `cpu` (use `cuda` only if GPU available) |
| `EFFICIENTNET_MODEL_PATH` | ✅ | Path to `.pth` file |

---

## Supabase: Switch to Service Role Key

For production, the backend should use the **service role key** (not anon key) so it can write to all tables without RLS issues:

1. Supabase → Settings → API
2. Copy **service_role** key (not anon)
3. Set as `SUPABASE_KEY` in your deployment env vars

> ⚠️ Never expose the service role key in `spectra.html` — it's backend-only.

The frontend (`spectra.html`) keeps using the **anon key** (already hardcoded in the JS) — this is correct and safe.

---

## After Deployment Checklist

- [ ] Backend `/health` endpoint returns `{"status": "healthy"}`
- [ ] `DEPLOYED_API_URL` set in `spectra.html`
- [ ] Model file uploaded to server (`/data/efficientnet_b0_spectra.pth`)
- [ ] Supabase OAuth → Authentication → URL Configuration: add your frontend URL to **Redirect URLs**
- [ ] Test image analysis end-to-end
- [ ] Test login/logout
