# BTC AI Platform

Plateforme d'analyse Bitcoin assistée par IA — chatbot quantitatif, dashboard, actualités, gestion de modèles.

## Architecture

```
btc-ai-platform/
├── backend/                 # FastAPI (Python)
│   ├── main.py              # Entry point
│   ├── api/                 # Routes API
│   │   ├── auth.py          # Auth (JWT + Supabase)
│   │   ├── chat.py          # Chatbot (SSE streaming)
│   │   ├── data.py          # Dataset (DuckDB + Parquet)
│   │   ├── news.py          # Actualités
│   │   └── models.py        # Modèles ML
│   ├── core/                # Logique métier
│   │   ├── config.py        # Configuration
│   │   ├── llm.py           # LLM Router (Gemini/Claude/Ollama)
│   │   ├── rag.py           # RAG Engine (pgvector)
│   │   ├── embeddings.py    # Embeddings (OpenAI)
│   │   ├── tools.py         # Function calling tools
│   │   └── agent.py         # System prompt
│   ├── db/                  # Base de données
│   │   ├── schema.sql       # Schéma PostgreSQL + pgvector
│   │   ├── supabase_client.py  # Client Supabase
│   │   └── duckdb_service.py   # Query Parquet via DuckDB
│   ├── services/            # Services
│   │   ├── news_service.py  # RSS + CryptoCompare + correlation
│   │   └── reports.py       # Génération rapports HTML/PDF
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                # Next.js 14 (App Router)
│   ├── app/
│   │   ├── layout.tsx       # Layout racine (dark mode)
│   │   ├── page.tsx         # Redirect → /dashboard
│   │   ├── login/           # Page de connexion
│   │   ├── dashboard/       # Dashboard (stats dataset)
│   │   ├── chat/            # Chatbot (streaming + markdown)
│   │   ├── news/            # Actualités (filtres par type)
│   │   ├── models/          # Gestion des modèles
│   │   ├── reports/         # Rapports
│   │   └── settings/        # Paramètres
│   ├── components/
│   │   ├── sidebar.tsx      # Navigation latérale
│   │   └── tradingview-widget.tsx  # Chart TradingView
│   ├── lib/
│   │   ├── api.ts           # Client API + streaming
│   │   ├── supabase.ts      # Client Supabase
│   │   └── utils.ts         # Helpers
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   └── Dockerfile
├── data/                    # Parquet files (monté depuis Drive/S3)
├── docker-compose.yml       # Dev local
└── README.md
```

## Stack technique

| Composant | Techno | Rôle |
|-----------|--------|------|
| Frontend | Next.js 14 + shadcn/ui + Tailwind | UI dark mode, SSR |
| Backend | FastAPI + Python | API REST + WebSocket |
| DB | Supabase (PostgreSQL + pgvector) | Users, conversations, embeddings, models |
| Query | DuckDB | SQL sur Parquet sans loader en RAM |
| LLM | Gemini 2.0 Flash (primaire) + Claude 3.5 (complexe) | Chatbot analyste |
| RAG | pgvector + OpenAI embeddings | Recherche documentaire |
| News | RSS + CryptoCompare | Actualités + corrélation |
| Auth | Supabase Auth (JWT) | Authentification sécurisée |
| Deploy | Vercel (frontend) + Railway (backend) | Production |

## Démarrage rapide

### 1. Backend

```bash
cd backend
cp .env.example .env
# Éditer .env avec vos clés API
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
cp .env.example .env.local
# Éditer .env.local avec vos clés
npm install
npm run dev
```

### 3. Docker (dev local)

```bash
docker-compose up
```

### 4. Base de données

Exécuter `backend/db/schema.sql` dans Supabase SQL Editor.

## Fonctionnalités MVP

- **Chatbot IA** — dialoguer avec le dataset (stats, schema, corrélations, sample)
- **Dashboard** — vue d'ensemble du dataset (lignes, colonnes, features, targets)
- **Actualités** — fetch RSS + CryptoCompare, filtre par type, corrélation prix
- **Modèles** — lister, comparer, voir métriques et features
- **Auth** — login/inscription via Supabase
- **Rapports** — génération HTML/PDF (à connecter)
- **Settings** — configuration LLM, notifications, sécurité

## Roadmap

- **MVP** ✅ — Chatbot + dashboard + news + auth
- **V1** — Model management + training pipeline + backtests + rapports auto
- **V2** — Multi-asset (ETH, SOL) + real-time + alertes IA + feature store
- **V3** — Fine-tuning + agent autonome + voice + mobile
