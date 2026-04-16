# MCP System — Deployment Guide
### Supabase (Database) + Render.com (Backend) + Vercel (Frontend) + cPanel (Subdomain)

---

## OVERVIEW

```
Your Domain (cPanel)
  └── api.yourdomain.com  → points to Render.com  (FastAPI backend)
  └── mcp.yourdomain.com  → points to Vercel       (Next.js frontend)

Render.com  ← runs FastAPI + connects to Supabase PostgreSQL
Vercel      ← runs Next.js + calls Render API
Supabase    ← PostgreSQL database (free tier)
```

---

## STEP 1 — Supabase (Database)

1. Go to **supabase.com** → Sign up free
2. Click **New Project** → fill name + password → choose region closest to you
3. Wait ~2 minutes for project to be ready
4. Go to **Settings** → **Database** → copy **Connection string (URI)**
   - It looks like: `postgresql://postgres:[PASSWORD]@db.xxxx.supabase.co:5432/postgres`
5. **Save this** — you'll need it in the next step

---

## STEP 2 — Push Code to GitHub

> Required so Render and Vercel can deploy from your code.

```bash
# On your PC, open terminal in G:/Ai-assitent/mcp-system
git init
git add .
git commit -m "Initial MCP System commit"

# Create new repo on github.com → copy the remote URL, then:
git remote add origin https://github.com/YOUR_USERNAME/mcp-system.git
git push -u origin main
```

---

## STEP 3 — Deploy Backend on Render.com

1. Go to **render.com** → Sign up (free) → **New** → **Web Service**
2. Connect your GitHub account → select your `mcp-system` repo
3. Configure:
   - **Name:** `mcp-system-backend`
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free
4. Click **Advanced** → **Add Environment Variables** (one by one):

   | Key | Value |
   |-----|-------|
   | `DATABASE_URL` | your Supabase connection string |
   | `GEMINI_API_KEY` | your Gemini API key |
   | `SECRET_KEY` | any random 32-char string |
   | `APP_ENV` | `production` |
   | `FRONTEND_URL` | `https://mcp.yourdomain.com` |
   | `CORS_ORIGINS` | `https://mcp.yourdomain.com` |
   | `SMTP_USER` | your Gmail address |
   | `SMTP_PASSWORD` | your Gmail App Password |
   | `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` |

5. Click **Create Web Service** → wait 3-5 minutes for build
6. You'll get a URL like: `https://mcp-system-backend.onrender.com`
7. **Test it:** open `https://mcp-system-backend.onrender.com/health` → should return `{"status":"healthy"}`

---

## STEP 4 — Deploy Frontend on Vercel

1. Go to **vercel.com** → Sign up with GitHub
2. Click **New Project** → import your `mcp-system` repo
3. Configure:
   - **Framework:** Next.js (auto-detected)
   - **Root Directory:** `frontend`
4. **Environment Variables:**

   | Key | Value |
   |-----|-------|
   | `NEXT_PUBLIC_API_URL` | `https://mcp-system-backend.onrender.com` |

5. Click **Deploy** → wait ~2 minutes
6. You'll get a URL like: `https://mcp-system.vercel.app`
7. **Test it:** open the URL → should see the login page

---

## STEP 5 — Set Up Subdomain in cPanel

> This makes your app available at `mcp.yourdomain.com`

### 5a — Create the Subdomain

1. Log in to **cPanel** (yourdomain.com/cpanel)
2. Find **Domains** → **Subdomains**
3. Create subdomain: `mcp` → yourdomain.com
4. Note the document root (e.g., `/public_html/mcp`) — you won't use it, but cPanel needs it

### 5b — Point Subdomain to Vercel (Frontend)

1. In cPanel → **Zone Editor** (or **DNS Zone Editor**)
2. Find or add a **CNAME record** for `mcp`:
   ```
   Name:  mcp
   Type:  CNAME
   Value: cname.vercel-dns.com
   TTL:   3600
   ```
3. In **Vercel Dashboard** → your project → **Settings** → **Domains**
4. Add domain: `mcp.yourdomain.com` → Vercel will verify and issue SSL automatically

### 5c — Point API Subdomain to Render (Backend)

1. In cPanel → **Zone Editor**, add another CNAME:
   ```
   Name:  api
   Type:  CNAME
   Value: mcp-system-backend.onrender.com
   TTL:   3600
   ```
2. In **Render Dashboard** → your web service → **Settings** → **Custom Domain**
3. Add: `api.yourdomain.com`
4. Render will show you a CNAME value to verify — use that value instead if different

### 5d — Update Environment Variables

After subdomain is live, update in **Vercel**:
```
NEXT_PUBLIC_API_URL = https://api.yourdomain.com
```

Update in **Render**:
```
FRONTEND_URL  = https://mcp.yourdomain.com
CORS_ORIGINS  = https://mcp.yourdomain.com
```

### DNS Propagation
Changes take **5 minutes to 48 hours** to propagate globally.
Check status: https://dnschecker.org

---

## STEP 6 — First Login

1. Open `https://mcp.yourdomain.com`
2. Click **Register** → create your admin account
3. Login → you're in the dashboard

---

## TROUBLESHOOTING

| Problem | Fix |
|---------|-----|
| Backend shows "Application error" | Check Render logs → Render Dashboard → Logs tab |
| `CORS error` in browser | Check `CORS_ORIGINS` env var in Render matches your frontend URL exactly |
| Database error on start | Verify `DATABASE_URL` is correct Supabase connection string |
| Frontend shows blank page | Check `NEXT_PUBLIC_API_URL` in Vercel env vars |
| Subdomain not working | Wait 24h for DNS propagation, check cPanel Zone Editor |
| Render spins down (free plan) | First request after idle takes 30s — upgrade to $7/mo Starter to avoid |
| Login fails | Check Supabase DB is accessible from Render (should work by default) |

---

## UPGRADE PATHS (When You're Ready)

| From | To | Cost | Benefit |
|------|----|------|---------|
| Render Free | Render Starter | $7/mo | No spin-down, always-on |
| Vercel Free | Vercel Pro | $20/mo | More builds, analytics |
| Supabase Free | Supabase Pro | $25/mo | No pause after 1 week inactivity |

**Minimum to keep app always-on:** Render Starter ($7/mo)

---

## PRODUCTION CHECKLIST

- [ ] `SECRET_KEY` is a random 32+ character string (not the default)
- [ ] `DATABASE_URL` points to Supabase
- [ ] `GEMINI_API_KEY` is set
- [ ] `CORS_ORIGINS` matches your exact frontend URL
- [ ] Both subdomains have SSL (green lock in browser)
- [ ] `/health` endpoint returns `{"status":"healthy"}`
- [ ] You can register + login successfully
- [ ] API docs accessible at `https://api.yourdomain.com/docs`
