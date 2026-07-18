"""SQLite database connection and initialization — replaces Supabase."""
import sqlite3
import json
import os
import threading
from pathlib import Path
from core.config import settings

DB_PATH = os.getenv("SQLITE_PATH", str(Path(__file__).resolve().parent.parent / "data" / "btc_ai.db"))

_local = threading.local()


def get_db() -> sqlite3.Connection:
    """Get a thread-local SQLite connection."""
    if not hasattr(_local, "conn"):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.conn = conn
    return _local.conn


def init_db():
    """Initialize all tables if they don't exist."""
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS profiles (
        id TEXT PRIMARY KEY,
        email TEXT NOT NULL UNIQUE,
        full_name TEXT,
        role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'analyst', 'admin')),
        avatar_url TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL DEFAULT 'New conversation',
        asset TEXT NOT NULL DEFAULT 'BTC',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
        content TEXT NOT NULL,
        llm_model TEXT,
        tokens_used INTEGER DEFAULT 0,
        tools_called TEXT DEFAULT '[]',
        metadata TEXT DEFAULT '{}',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);
    CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id);

    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        doc_type TEXT NOT NULL CHECK (doc_type IN ('report', 'documentation', 'log', 'news', 'model_card', 'config', 'other')),
        source TEXT,
        asset TEXT DEFAULT 'BTC',
        url TEXT,
        tags TEXT DEFAULT '[]',
        embedding TEXT,
        metadata TEXT DEFAULT '{}',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_doc_type ON documents(doc_type);
    CREATE INDEX IF NOT EXISTS idx_doc_asset ON documents(asset);

    CREATE TABLE IF NOT EXISTS news_events (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        summary TEXT,
        content TEXT,
        source TEXT NOT NULL,
        url TEXT,
        event_type TEXT NOT NULL CHECK (event_type IN ('fed', 'cpi', 'rate', 'etf', 'halving', 'liquidation', 'hack', 'regulation', 'market', 'whale', 'mining', 'other')),
        sentiment REAL DEFAULT 0.0,
        entities TEXT DEFAULT '[]',
        asset TEXT DEFAULT 'BTC',
        price_at_event REAL,
        price_change_24h REAL,
        event_date TEXT NOT NULL,
        embedding TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_news_date ON news_events(event_date DESC);
    CREATE INDEX IF NOT EXISTS idx_news_type ON news_events(event_type);

    CREATE TABLE IF NOT EXISTS model_runs (
        id TEXT PRIMARY KEY,
        model_name TEXT NOT NULL,
        model_type TEXT NOT NULL CHECK (model_type IN ('lstm', 'transformer', 'xgboost', 'lightgbm', 'ensemble', 'other')),
        version TEXT NOT NULL,
        asset TEXT NOT NULL DEFAULT 'BTC',
        hyperparams TEXT DEFAULT '{}',
        metrics TEXT DEFAULT '{}',
        features_used TEXT DEFAULT '[]',
        target_col TEXT,
        train_start TEXT,
        train_end TEXT,
        val_start TEXT,
        val_end TEXT,
        test_start TEXT,
        test_end TEXT,
        train_loss REAL,
        val_loss REAL,
        test_loss REAL,
        status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'archived')),
        model_path TEXT,
        checkpoint_path TEXT,
        tensorboard_path TEXT,
        notes TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_runs_asset ON model_runs(asset);
    CREATE INDEX IF NOT EXISTS idx_runs_status ON model_runs(status);
    CREATE INDEX IF NOT EXISTS idx_runs_created ON model_runs(created_at DESC);

    CREATE TABLE IF NOT EXISTS dataset_metadata (
        id TEXT PRIMARY KEY,
        asset TEXT NOT NULL DEFAULT 'BTC',
        version TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size_bytes INTEGER,
        n_rows INTEGER,
        n_columns INTEGER,
        n_features INTEGER,
        n_targets INTEGER,
        start_date TEXT,
        end_date TEXT,
        granularity TEXT DEFAULT '1m',
        columns TEXT DEFAULT '{}',
        stats TEXT DEFAULT '{}',
        quality_report TEXT DEFAULT '{}',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS feature_importance (
        id TEXT PRIMARY KEY,
        model_run_id TEXT NOT NULL,
        feature_name TEXT NOT NULL,
        importance REAL NOT NULL,
        method TEXT DEFAULT 'shap',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (model_run_id) REFERENCES model_runs(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_fi_model ON feature_importance(model_run_id);

    CREATE TABLE IF NOT EXISTS backtest_results (
        id TEXT PRIMARY KEY,
        model_run_id TEXT NOT NULL,
        asset TEXT NOT NULL DEFAULT 'BTC',
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        initial_capital REAL,
        final_capital REAL,
        total_return REAL,
        sharpe_ratio REAL,
        max_drawdown REAL,
        win_rate REAL,
        n_trades INTEGER,
        metrics TEXT DEFAULT '{}',
        trades TEXT DEFAULT '[]',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (model_run_id) REFERENCES model_runs(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS reports (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        report_type TEXT NOT NULL DEFAULT 'training',
        status TEXT NOT NULL DEFAULT 'completed',
        content TEXT DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    -- Insert default admin user if not exists
    INSERT OR IGNORE INTO profiles (id, email, full_name, role)
    VALUES ('local-user-001', 'admin@btc-ai.local', 'Admin Local', 'admin');
    """)
    db.commit()


def _uuid():
    import uuid
    return str(uuid.uuid4())


def _parse_json(val):
    """Parse JSON field from SQLite, return None if empty."""
    if not val:
        return None
    try:
        return json.loads(val)
    except Exception:
        return val


def _row_to_dict(row):
    """Convert sqlite3.Row to dict, parsing JSON fields."""
    if row is None:
        return None
    d = dict(row)
    for k, v in list(d.items()):
        if k in ("tags", "entities", "features_used", "tools_called", "metadata", "hyperparams", "metrics", "columns", "stats", "quality_report", "trades"):
            d[k] = _parse_json(v) or ([] if k in ("tags", "entities", "features_used", "tools_called", "trades") else {})
    return d
