#!/bin/bash
set -e

echo "============================================"
echo "  BTC AI Platform - Setup"
echo "============================================"
echo ""

echo "[1/4] Backend: installing Python dependencies..."
cd backend
pip install -r requirements.txt
cd ..

echo ""
echo "[2/4] Frontend: installing Node dependencies..."
cd frontend
npm install
cd ..

echo ""
echo "[3/4] Checking .env files..."
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "  Created backend/.env - EDIT IT with your API keys!"
else
    echo "  backend/.env already exists"
fi
if [ ! -f frontend/.env.local ]; then
    cp frontend/.env.local.example frontend/.env.local
    echo "  Created frontend/.env.local - EDIT IT with your Supabase keys!"
else
    echo "  frontend/.env.local already exists"
fi

echo ""
echo "[4/4] Setup complete!"
echo ""
echo "NEXT STEPS:"
echo "  1. Edit backend/.env with your API keys (Gemini, Supabase, etc.)"
echo "  2. Edit frontend/.env.local with your Supabase URL and anon key"
echo "  3. Run schema.sql in Supabase SQL Editor"
echo "  4. Copy btc_enriched_dataset_1m.parquet to data/"
echo "  5. Start backend:  cd backend && uvicorn main:app --reload"
echo "  6. Start frontend: cd frontend && npm run dev"
echo "  7. Open http://localhost:3000"
echo ""
