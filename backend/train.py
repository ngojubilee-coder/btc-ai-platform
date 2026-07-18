"""BTC AI Platform - Pipeline d'entrainement local complet.

Utilisation:
    python train.py                    # Entrainement par defaut (XGBoost)
    python train.py --model lstm       # Entrainement LSTM
    python train.py --model xgboost    # Entrainement XGBoost
    python train.py --model random_forest
    python train.py --list             # Lister les modeles disponibles
    python train.py --backtest         # Backtest apres entrainement
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# Charger .env
from dotenv import load_dotenv
load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", "../data")
PARQUET_PATH = os.getenv("PARQUET_PATH", "../data/btc_enriched_dataset_1m.parquet")


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    colors = {"INFO": "\033[36m", "OK": "\033[32m", "WARN": "\033[33m", "ERR": "\033[31m"}
    reset = "\033[0m"
    color = colors.get(level, "")
    print(f"  {color}[{ts}] [{level}]{reset} {msg}")


def load_dataset():
    """Charger le dataset parquet."""
    log(f"Chargement du dataset: {PARQUET_PATH}")
    if not os.path.exists(PARQUET_PATH):
        log(f"Fichier parquet introuvable: {PARQUET_PATH}", "ERR")
        log("Placez le fichier btc_enriched_dataset_1m.parquet dans le dossier data/", "WARN")
        log("Ou telechargez-le avec: python download_data.py", "WARN")
        return None

    df = pd.read_parquet(PARQUET_PATH)
    log(f"Dataset charge: {len(df)} lignes, {len(df.columns)} colonnes", "OK")

    # Identifier les features et targets
    target_cols = [c for c in df.columns if c.startswith("target_")]
    feature_cols = [c for c in df.columns if not c.startswith("target_") and c != "timestamp"]

    log(f"Features: {len(feature_cols)} | Targets: {len(target_cols)}")

    return df, feature_cols, target_cols


def prepare_data(df, feature_cols, target_col="target_return_15m", test_size=0.2):
    """Preparer les donnees pour l'entrainement."""
    log(f"Preparation des donnees (target: {target_col})...")

    # Supprimer les lignes avec des NaN sur la target
    df_clean = df.dropna(subset=[target_col])

    X = df_clean[feature_cols].fillna(0)
    y = df_clean[target_col]

    # Classification: return > 0 = 1, sinon 0
    y_class = (y > 0).astype(int)

    split_idx = int(len(df_clean) * (1 - test_size))

    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y_class.iloc[:split_idx], y_class.iloc[split_idx:]

    log(f"Train: {len(X_train)} | Test: {len(X_test)} | Split: {split_idx}", "OK")

    return X_train, X_test, y_train, y_test


def train_xgboost(X_train, X_test, y_train, y_test):
    """Entrainement XGBoost."""
    log("Entrainement XGBoost...")
    try:
        from xgboost import XGBClassifier
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

        model = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric="logloss",
        )

        t0 = time.time()
        model.fit(X_train, y_train)
        train_time = time.time() - t0

        y_pred = model.predict(X_test)

        metrics = {
            "model": "xgboost",
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "f1": float(f1_score(y_test, y_pred, zero_division=0)),
            "train_time_sec": round(train_time, 2),
            "n_features": X_train.shape[1],
            "n_train": X_train.shape[0],
            "n_test": X_test.shape[0],
        }

        # Feature importance
        importance = dict(zip(X_train.columns, model.feature_importances_))
        importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True)[:20])
        metrics["top_features"] = importance

        log(f"XGBoost entraine en {train_time:.1f}s", "OK")
        log(f"  Accuracy: {metrics['accuracy']:.4f}", "OK")
        log(f"  F1 Score: {metrics['f1']:.4f}", "OK")
        log(f"  Top feature: {list(importance.keys())[0]} ({list(importance.values())[0]:.4f})", "OK")

        # Sauvegarder le modele
        model_path = os.path.join(DATA_DIR, "models", "xgboost_model.json")
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        model.save_model(model_path)
        log(f"Modele sauvegarde: {model_path}", "OK")

        return metrics, model
    except ImportError:
        log("xgboost non installe. Installation...", "WARN")
        os.system(f"{sys.executable} -m pip install xgboost scikit-learn")
        return train_xgboost(X_train, X_test, y_train, y_test)


def train_random_forest(X_train, X_test, y_train, y_test):
    """Entrainement Random Forest."""
    log("Entrainement Random Forest...")
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1,
        )

        t0 = time.time()
        model.fit(X_train, y_train)
        train_time = time.time() - t0

        y_pred = model.predict(X_test)

        metrics = {
            "model": "random_forest",
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "f1": float(f1_score(y_test, y_pred, zero_division=0)),
            "train_time_sec": round(train_time, 2),
            "n_features": X_train.shape[1],
            "n_train": X_train.shape[0],
            "n_test": X_test.shape[0],
        }

        importance = dict(zip(X_train.columns, model.feature_importances_))
        importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True)[:20])
        metrics["top_features"] = importance

        log(f"Random Forest entraine en {train_time:.1f}s", "OK")
        log(f"  Accuracy: {metrics['accuracy']:.4f}", "OK")
        log(f"  F1 Score: {metrics['f1']:.4f}", "OK")

        return metrics, model
    except ImportError:
        log("scikit-learn non installe. Installation...", "WARN")
        os.system(f"{sys.executable} -m pip install scikit-learn")
        return train_random_forest(X_train, X_test, y_train, y_test)


def train_lstm(X_train, X_test, y_train, y_test):
    """Entrainement LSTM (TensorFlow/Keras)."""
    log("Entrainement LSTM...")
    try:
        import tensorflow as tf
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout
        from tensorflow.keras.optimizers import Adam

        # Reshape pour LSTM: [samples, timesteps, features]
        n_features = X_train.shape[1]
        X_train_reshaped = X_train.values.reshape(-1, 1, n_features)
        X_test_reshaped = X_test.values.reshape(-1, 1, n_features)

        model = Sequential([
            LSTM(64, return_sequences=True, input_shape=(1, n_features)),
            Dropout(0.2),
            LSTM(32),
            Dropout(0.2),
            Dense(16, activation="relu"),
            Dense(1, activation="sigmoid"),
        ])

        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss="binary_crossentropy",
            metrics=["accuracy"],
        )

        t0 = time.time()
        history = model.fit(
            X_train_reshaped, y_train,
            epochs=20,
            batch_size=256,
            validation_split=0.1,
            verbose=1,
        )
        train_time = time.time() - t0

        loss, accuracy = model.evaluate(X_test_reshaped, y_test, verbose=0)

        metrics = {
            "model": "lstm",
            "accuracy": float(accuracy),
            "val_loss": float(loss),
            "train_time_sec": round(train_time, 2),
            "n_features": n_features,
            "n_train": X_train.shape[0],
            "n_test": X_test.shape[0],
            "epochs": 20,
        }

        log(f"LSTM entraine en {train_time:.1f}s", "OK")
        log(f"  Accuracy: {metrics['accuracy']:.4f}", "OK")
        log(f"  Val Loss: {metrics['val_loss']:.4f}", "OK")

        # Sauvegarder
        model_path = os.path.join(DATA_DIR, "models", "lstm_model.keras")
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        model.save(model_path)
        log(f"Modele sauvegarde: {model_path}", "OK")

        return metrics, model
    except ImportError:
        log("TensorFlow non installe. Installation...", "WARN")
        os.system(f"{sys.executable} -m pip install tensorflow")
        return train_lstm(X_train, X_test, y_train, y_test)


def run_backtest(model, X_test, y_test, model_type="xgboost"):
    """Backtest simple du modele."""
    log("Backtest en cours...")

    if model_type == "lstm":
        import tensorflow as tf
        y_pred = (model.predict(X_test.values.reshape(-1, 1, X_test.shape[1])) > 0.5).astype(int).flatten()
    else:
        y_pred = model.predict(X_test)

    # Simuler un trading simple: acheter si pred=1
    correct = (y_pred == y_test.values).sum()
    total = len(y_test)
    win_rate = correct / total * 100

    # Calculer le PnL simule
    returns = y_test.values  # 1 = hausse, 0 = baisse
    pnl = 0
    for i in range(len(y_pred)):
        if y_pred[i] == 1:  # On achete
            pnl += 1 if returns[i] == 1 else -1

    log(f"Backterm Resultats:", "OK")
    log(f"  Win rate: {win_rate:.2f}%", "OK")
    log(f"  Trades gagnants: {correct}/{total}", "OK")
    log(f"  PnL simule: {pnl:+d} (unites)", "OK")

    return {"win_rate": win_rate, "correct": int(correct), "total": int(total), "pnl": int(pnl)}


def save_results(metrics, backtest=None):
    """Sauvegarder les resultats en JSON."""
    results_dir = os.path.join(DATA_DIR, "results")
    os.makedirs(results_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Convertir les valeurs numpy en types Python natifs
    def convert(obj):
        if isinstance(obj, (np.float32, np.float64, np.int32, np.int64)):
            return obj.item()
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [convert(v) for v in obj]
        return obj

    result = {
        "timestamp": timestamp,
        "metrics": convert(metrics),
        "backtest": convert(backtest),
    }

    filepath = os.path.join(results_dir, f"train_{metrics['model']}_{timestamp}.json")
    with open(filepath, "w") as f:
        json.dump(result, f, indent=2)

    log(f"Resultats sauvegardes: {filepath}", "OK")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="BTC AI Platform - Entrainement")
    parser.add_argument("--model", type=str, default="xgboost",
                        choices=["xgboost", "random_forest", "lstm"],
                        help="Type de modele a entrainer")
    parser.add_argument("--target", type=str, default="target_return_15m",
                        help="Colonne target a predire")
    parser.add_argument("--backtest", action="store_true",
                        help="Lancer un backtest apres l'entrainement")
    parser.add_argument("--list", action="store_true",
                        help="Lister les modeles disponibles")
    args = parser.parse_args()

    if args.list:
        log("Modeles disponibles:")
        log("  - xgboost       (Gradient Boosting, rapide, performant)")
        log("  - random_forest (Random Forest, robuste)")
        log("  - lstm           (Deep Learning, TensorFlow/Keras)")
        return

    print("\n  ╔══════════════════════════════════════════════════════╗")
    print("  ║     BTC AI PLATFORM - PIPELINE D'ENTRAINEMENT        ║")
    print("  ╚══════════════════════════════════════════════════════╝\n")

    # 1. Charger les donnees
    result = load_dataset()
    if result is None:
        sys.exit(1)
    df, feature_cols, target_cols = result

    if args.target not in target_cols:
        log(f"Target '{args.target}' non trouvee. Targets disponibles: {target_cols}", "ERR")
        sys.exit(1)

    # 2. Preparer les donnees
    X_train, X_test, y_train, y_test = prepare_data(df, feature_cols, target_col=args.target)

    # 3. Entrainement
    log(f"Demarrage de l'entrainement: {args.model}")
    print()

    if args.model == "xgboost":
        metrics, model = train_xgboost(X_train, X_test, y_train, y_test)
    elif args.model == "random_forest":
        metrics, model = train_random_forest(X_train, X_test, y_train, y_test)
    elif args.model == "lstm":
        metrics, model = train_lstm(X_train, X_test, y_train, y_test)

    # 4. Backtest optionnel
    backtest = None
    if args.backtest:
        print()
        backtest = run_backtest(model, X_test, y_test, model_type=args.model)

    # 5. Sauvegarder
    print()
    save_results(metrics, backtest)

    # 6. Resume
    print("\n  ╔══════════════════════════════════════════════════════╗")
    print("  ║     ENTRAINEMENT TERMINE                             ║")
    print("  ╠══════════════════════════════════════════════════════╣")
    print(f"  ║  Modele:    {args.model:<42}║")
    print(f"  ║  Accuracy:  {metrics['accuracy']:<42.4f}║")
    print(f"  ║  Temps:     {metrics['train_time_sec']:<41.1f}s║")
    if backtest:
        print(f"  ║  Win rate:  {backtest['win_rate']:<41.2f}%║")
    print("  ╚══════════════════════════════════════════════════════╝\n")


if __name__ == "__main__":
    main()
