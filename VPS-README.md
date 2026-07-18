# BTC AI Platform — VPS Windows (Tout Inclus)

## Installation rapide (3 etapes)

```bat
1. install-vps.bat        :: Installe Python, Node.js, dependances, .env
2. prepare-data.bat       :: Genere le dataset BTC pour l'entrainement
3. start-vps.bat          :: Demarre backend + frontend en local
```

## Scripts disponibles

| Script | Description |
|--------|-------------|
| `install-vps.bat` | Installation complete (Python, Node, deps, venv, .env) |
| `start-vps.bat` | Demarre backend (8000) + frontend (3000) |
| `stop-vps.bat` | Arrete tous les services |
| `train-vps.bat` | Menu d'entrainement (XGBoost, Random Forest, LSTM) |
| `prepare-data.bat` | Genere le dataset BTC synthetique |

## URLs locales

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health

## Entrainement

### Menu interactif
```bat
train-vps.bat
```

### En ligne de commande
```bash
cd backend
python train.py --model xgboost --backtest
python train.py --model random_forest --backtest
python train.py --model lstm --backtest
python train.py --list                    # Lister les modeles
```

### Modeles disponibles
- **XGBoost** — Gradient Boosting, rapide, performant (recommande)
- **Random Forest** — Robuste, bon pour baseline
- **LSTM** — Deep Learning (TensorFlow/Keras), plus lent mais puissant

## Configuration

### Fichier `backend/.env`
```ini
# Cles API (optionnel pour l'entrainement local)
GEMINI_API_KEY=your-key
SUPABASE_URL=your-url
SUPABASE_KEY=your-key

# Donnees
DATA_DIR=../data
PARQUET_PATH=../data/btc_enriched_dataset_1m.parquet

# Serveur
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:3000
```

### Fichier `frontend/.env.local`
```ini
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Structure du projet

```
btc-ai-platform/
  install-vps.bat          :: Installation
  start-vps.bat            :: Demarrage
  stop-vps.bat             :: Arret
  train-vps.bat            :: Entrainement
  prepare-data.bat         :: Donnees
  backend/
    train.py               :: Pipeline d'entrainement
    download_data.py       :: Generation dataset
    main.py                :: API FastAPI
    requirements.txt
    .env                   :: Configuration
  frontend/
    package.json
    .env.local             :: URL du backend
  data/
    btc_enriched_dataset_1m.parquet  :: Dataset
    models/                :: Modeles sauvegardes
    results/               :: Resultats d'entrainement
```

## Deploiement Cloudflare (optionnel)

Si vous voulez aussi deployer le frontend sur Cloudflare:
```bash
cd frontend
npm run deploy:cloudflare
```

## Deploiement Railway (backend en ligne)

Si vous voulez exposer le backend sur internet:
```bash
npm install -g @railway/cli
railway login
cd backend
railway init --name btc-ai-platform
railway up --detach
railway domain
```
Puis mettez a jour `frontend/.env.local` avec l'URL Railway.
