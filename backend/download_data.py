"""Telecharger ou generer le dataset BTC pour l'entrainement.

Usage:
    python download_data.py              # Generer un dataset synthetique
    python download_data.py --real       # Telecharger les vraies donnees BTC (si disponible)
"""
import argparse
import io
import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Forcer UTF-8 sur Windows
if sys.platform == "win32" and __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", "../data")
PARQUET_PATH = os.getenv("PARQUET_PATH", "../data/btc_enriched_dataset_1m.parquet")


def generate_synthetic_dataset(n_rows=100000):
    """Generer un dataset BTC synthetique realiste pour l'entrainement."""
    print(f"  Generation d'un dataset synthetique ({n_rows} lignes)...")

    np.random.seed(42)
    
    # Timestamps: 1 minute d'intervalle
    start_date = datetime(2023, 1, 1)
    timestamps = [start_date + timedelta(minutes=i) for i in range(n_rows)]

    # Prix BTC: random walk avec volatilite
    returns = np.random.normal(0.0001, 0.002, n_rows)
    price = 40000 * np.cumprod(1 + returns)

    # Volume
    volume = np.random.lognormal(15, 1, n_rows)

    # Indicateurs techniques
    df = pd.DataFrame({
        "timestamp": timestamps,
        "price_close": price,
        "price_open": price * (1 + np.random.normal(0, 0.001, n_rows)),
        "price_high": price * (1 + np.abs(np.random.normal(0, 0.002, n_rows))),
        "price_low": price * (1 - np.abs(np.random.normal(0, 0.002, n_rows))),
        "volume": volume,
    })

    # Moving averages
    for window in [7, 14, 30, 60, 120]:
        df[f"sma_{window}"] = df["price_close"].rolling(window).mean()
        df[f"ema_{window}"] = df["price_close"].ewm(span=window).mean()

    # RSI
    delta = df["price_close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / (loss + 1e-10)
    df["rsi_14"] = 100 - (100 / (1 + rs))

    # MACD
    ema_12 = df["price_close"].ewm(span=12).mean()
    ema_26 = df["price_close"].ewm(span=26).mean()
    df["macd"] = ema_12 - ema_26
    df["macd_signal"] = df["macd"].ewm(span=9).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    # Bollinger Bands
    sma_20 = df["price_close"].rolling(20).mean()
    std_20 = df["price_close"].rolling(20).std()
    df["bb_upper"] = sma_20 + 2 * std_20
    df["bb_lower"] = sma_20 - 2 * std_20
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / sma_20

    # Volatilite
    df["volatility_15m"] = df["price_close"].pct_change().rolling(15).std()
    df["volatility_60m"] = df["price_close"].pct_change().rolling(60).std()

    # Volume indicators
    df["volume_sma_30"] = df["volume"].rolling(30).mean()
    df["volume_ratio"] = df["volume"] / (df["volume_sma_30"] + 1e-10)

    # Targets: return futur > 0 ?
    for horizon in [5, 15, 30, 60]:
        future_return = df["price_close"].shift(-horizon) / df["price_close"] - 1
        df[f"target_return_{horizon}m"] = future_return

    # Remplir les NaN
    df = df.bfill().fillna(0)

    # Sauvegarder
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = PARQUET_PATH
    df.to_parquet(filepath, index=False)
    
    file_size = os.path.getsize(filepath) / (1024 * 1024)
    print(f"  Dataset sauvegarde: {filepath}")
    print(f"  Taille: {file_size:.1f} MB")
    print(f"  Lignes: {len(df)} | Colonnes: {len(df.columns)}")
    
    # Afficher les colonnes
    feature_cols = [c for c in df.columns if not c.startswith("target_") and c != "timestamp"]
    target_cols = [c for c in df.columns if c.startswith("target_")]
    print(f"  Features: {len(feature_cols)} | Targets: {len(target_cols)}")
    print(f"  Targets: {target_cols}")

    return df


def main():
    parser = argparse.ArgumentParser(description="Telecharger/generer le dataset BTC")
    parser.add_argument("--real", action="store_true", help="Tenter de telecharger les vraies donnees")
    parser.add_argument("--rows", type=int, default=100000, help="Nombre de lignes (dataset synthetique)")
    args = parser.parse_args()

    print("\n  === BTC AI Platform - Preparation du Dataset ===\n")

    if args.real:
        print("  Tentative de telechargement des vraies donnees BTC...")
        try:
            import yfinance as yf
            btc = yf.download("BTC-USD", period="2y", interval="1m")
            if len(btc) > 0:
                print(f"  Donnees telechargees: {len(btc)} lignes")
                # TODO: enrichir avec les indicateurs
                os.makedirs(DATA_DIR, exist_ok=True)
                btc.to_parquet(PARQUET_PATH)
                print(f"  Sauvegarde: {PARQUET_PATH}")
                return
        except ImportError:
            print("  yfinance non installe. Utilisation du dataset synthetique.")
        except Exception as e:
            print(f"  Erreur: {e}. Utilisation du dataset synthetique.")

    # Dataset synthetique par defaut
    generate_synthetic_dataset(n_rows=args.rows)
    print("\n  Dataset pret pour l'entrainement!\n")


if __name__ == "__main__":
    main()
