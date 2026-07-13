# BTC AI Platform — Deployment Guide

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Cloudflare      │────▶│  Backend API      │────▶│  Supabase DB    │
│  Pages (Frontend)│     │  (Docker/VPS)     │     │  (Postgres)     │
│  Next.js + React │     │  FastAPI + Python │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │  LLM Provider     │
                        │  Gemini/Claude/   │
                        │  OpenAI/Ollama    │
                        └──────────────────┘
```

## Frontend — Cloudflare Pages

### Prerequisites
- Node.js 20+
- Cloudflare account (free tier works)
- Wrangler CLI

### Step 1: Install dependencies
```bash
cd frontend
npm install
```

### Step 2: Configure environment
Create `.env.local` with your production values:
```env
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### Step 3: Build and preview locally
```bash
npm run preview
```
This builds the app with OpenNext and runs it in the Workers runtime locally.

### Step 4: Deploy to Cloudflare
```bash
npm run deploy:cloudflare
```

### Step 5: Set environment variables in Cloudflare Dashboard
1. Go to Cloudflare Dashboard > Workers & Pages
2. Select your project `btc-ai-platform`
3. Settings > Environment Variables
4. Add:
   - `NEXT_PUBLIC_API_URL` = your backend URL
   - `NEXT_PUBLIC_SUPABASE_URL` = your Supabase URL
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` = your Supabase anon key

### Alternative: Git Integration (CI/CD)
1. Push your code to GitHub
2. Cloudflare Dashboard > Pages > Create a project > Connect to Git
3. Set build command: `npm run build:cloudflare`
4. Set output directory: `.open-next`
5. Add environment variables
6. Every push to main branch triggers automatic deployment

## Backend — Docker / VPS / PaaS

### Option 1: Docker (Recommended)
```bash
# Build and run
docker-compose up -d --build

# Backend will be available at http://localhost:8000
```

### Option 2: Railway / Render
1. Connect GitHub repo
2. Set root directory to `backend/`
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add all environment variables from `backend/.env.example`

### Option 3: Fly.io (Edge deployment)
```bash
cd backend
fly launch --dockerfile Dockerfile
fly deploy
```

### Backend Environment Variables
See `backend/.env.example` for the full list. Critical ones:
- `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`
- `GEMINI_API_KEY` (or `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`)
- `JWT_SECRET` — **change this in production!**
- `CORS_ORIGINS` — set to your Cloudflare Pages URL
- `PARQUET_PATH` — path to your dataset file

## Security Checklist (B2B Production)

- [ ] Change `JWT_SECRET` to a strong random value
- [ ] Set `CORS_ORIGINS` to only your frontend domain(s)
- [ ] Enable Supabase RLS (Row Level Security) policies
- [ ] Set up Supabase email confirmations
- [ ] Configure rate limiting (already built-in: 100 req/min)
- [ ] Enable Cloudflare WAF and DDoS protection
- [ ] Set up Cloudflare Access for admin routes
- [ ] Use HTTPS only (Cloudflare provides SSL automatically)
- [ ] Set secure headers (already configured in next.config.js)
- [ ] Monitor API health via `/health` endpoint

## Custom Domain Setup

1. Cloudflare Dashboard > Workers & Pages > your project
2. Custom domains > Set up a custom domain
3. Add your domain (e.g., `app.yourdomain.com`)
4. Cloudflare will handle DNS and SSL automatically

## Monitoring

- **Frontend**: Cloudflare Analytics dashboard
- **Backend**: `/health` endpoint provides component status
- **Logs**: Cloudflare Workers logs + backend stdout
- **Uptime**: Set up Cloudflare Workers for uptime monitoring

## Deploy Popup

The app includes a built-in deployment popup (floating button bottom-left).
It shows:
- API, Database, and LLM health status
- Frontend and backend URLs
- Deployment commands
- Environment variable reference
- B2B production checklist
