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
| `train-vps.bat` | Menu d'entrainement (XGBoost, RF, LSTM, Comparaison) |
| `prepare-data.bat` | Genere le dataset BTC synthetique |
| `health-check-vps.bat` | Verifie backend, frontend, API, dataset, modeles |
| `monitoring-vps.bat` | Statut systeme: ports, disque, config, modeles |
| `backup-vps.bat` | Backup config + modeles + dataset en ZIP |
| `update-vps.bat` | Git pull + mise a jour deps + tests |
| `auto-train-vps.bat` | Entrainement automatique (arg: modele) + log |
| `setup-scheduled-task.bat` | Planifie entrainement via Task Scheduler |

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
python train.py --compare --backtest       # Comparer tous les modeles + CSV
python train.py --list                    # Lister les modeles
python train.py --target target_return_5m  # Changer la target
```

### Modeles disponibles
- **XGBoost** — Gradient Boosting, rapide, performant (recommande)
- **Random Forest** — Robuste, bon pour baseline
- **LSTM** — Deep Learning (TensorFlow/Keras), plus lent mais puissant

### Entrainement automatique
```bat
:: Entrainement XGBoost avec log
auto-train-vps.bat xgboost

:: Comparaison tous modeles
auto-train-vps.bat compare

:: Planifier via Windows Task Scheduler
setup-scheduled-task.bat
```

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
  install-vps.bat          :: Installation complete
  start-vps.bat            :: Demarrage backend + frontend
  stop-vps.bat             :: Arret des services
  train-vps.bat            :: Menu d'entrainement (6 options)
  prepare-data.bat         :: Generation dataset
  health-check-vps.bat     :: Verification systeme
  monitoring-vps.bat       :: Monitoring complet
  backup-vps.bat           :: Backup ZIP
  update-vps.bat           :: Mise a jour git + deps
  auto-train-vps.bat       :: Entrainement automatique + log
  setup-scheduled-task.bat :: Planification Task Scheduler
  backend/
    train.py               :: Pipeline d'entrainement (--compare, --backtest)
    download_data.py       :: Generation dataset BTC
    main.py                :: API FastAPI
    api/training.py        :: Router API training (status, results, models)
    requirements.txt       :: Deps Python (incluant xgboost, sklearn)
    .env                   :: Configuration
    tests/                 :: 104 tests unitaires
  frontend/
    package.json
    .env.local             :: URL du backend
    app/dashboard/training/ :: Page dashboard entrainement
  data/
    btc_enriched_dataset_1m.parquet  :: Dataset
    whale_wallets_list.csv           :: 211 wallets baleine connus
    models/                :: Modeles sauvegardes (.json, .keras)
    results/               :: Resultats JSON + CSV comparaison
    training_log.txt       :: Log entrainement automatique
```

## Verification systeme

```bat
health-check-vps.bat    :: Verifie backend, frontend, API, dataset, modeles
monitoring-vps.bat      :: Statut complet: ports, disque, config, Python, Node
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
