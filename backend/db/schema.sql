-- ============================================================
-- BTC AI Platform — Schéma de base de données
-- À exécuter dans Supabase SQL Editor
-- ============================================================

-- Extension pgvector pour la recherche sémantique
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- USERS (géré par Supabase Auth, table de profil)
-- ============================================================
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'analyst', 'admin')),
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- CONVERSATIONS & MESSAGES
-- ============================================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'New conversation',
    asset TEXT NOT NULL DEFAULT 'BTC',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    llm_model TEXT,
    tokens_used INTEGER DEFAULT 0,
    tools_called JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);

-- ============================================================
-- DOCUMENTS (RAG — rapports, docs, logs, actualités)
-- ============================================================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    doc_type TEXT NOT NULL CHECK (doc_type IN ('report', 'documentation', 'log', 'news', 'model_card', 'config', 'other')),
    source TEXT,
    asset TEXT DEFAULT 'BTC',
    url TEXT,
    tags TEXT[] DEFAULT '{}',
    embedding VECTOR(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_documents_asset ON documents(asset);
CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================
-- NEWS EVENTS (actualités crypto + macro)
-- ============================================================
CREATE TABLE IF NOT EXISTS news_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    summary TEXT,
    content TEXT,
    source TEXT NOT NULL,
    url TEXT,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'fed', 'cpi', 'rate', 'etf', 'halving', 'liquidation',
        'hack', 'regulation', 'market', 'whale', 'mining', 'other'
    )),
    sentiment FLOAT DEFAULT 0.0,
    entities TEXT[] DEFAULT '{}',
    asset TEXT DEFAULT 'BTC',
    price_at_event FLOAT,
    price_change_24h FLOAT,
    event_date TIMESTAMPTZ NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_news_date ON news_events(event_date DESC);
CREATE INDEX IF NOT EXISTS idx_news_type ON news_events(event_type);
CREATE INDEX IF NOT EXISTS idx_news_asset ON news_events(asset);
CREATE INDEX IF NOT EXISTS idx_news_embedding ON news_events USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================
-- MODEL RUNS (tracking des entraînements)
-- ============================================================
CREATE TABLE IF NOT EXISTS model_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name TEXT NOT NULL,
    model_type TEXT NOT NULL CHECK (model_type IN ('lstm', 'transformer', 'xgboost', 'lightgbm', 'ensemble', 'other')),
    version TEXT NOT NULL,
    asset TEXT NOT NULL DEFAULT 'BTC',
    hyperparams JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    features_used TEXT[] DEFAULT '{}',
    target_col TEXT,
    train_start TIMESTAMPTZ,
    train_end TIMESTAMPTZ,
    val_start TIMESTAMPTZ,
    val_end TIMESTAMPTZ,
    test_start TIMESTAMPTZ,
    test_end TIMESTAMPTZ,
    train_loss FLOAT,
    val_loss FLOAT,
    test_loss FLOAT,
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'archived')),
    model_path TEXT,
    checkpoint_path TEXT,
    tensorboard_path TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_model_runs_asset ON model_runs(asset);
CREATE INDEX IF NOT EXISTS idx_model_runs_status ON model_runs(status);
CREATE INDEX IF NOT EXISTS idx_model_runs_created ON model_runs(created_at DESC);

-- ============================================================
-- DATASET METADATA
-- ============================================================
CREATE TABLE IF NOT EXISTS dataset_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset TEXT NOT NULL DEFAULT 'BTC',
    version TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size_bytes BIGINT,
    n_rows BIGINT,
    n_columns INTEGER,
    n_features INTEGER,
    n_targets INTEGER,
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    granularity TEXT DEFAULT '1m',
    columns JSONB DEFAULT '{}',
    stats JSONB DEFAULT '{}',
    quality_report JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_dataset_asset ON dataset_metadata(asset);
CREATE INDEX IF NOT EXISTS idx_dataset_version ON dataset_metadata(version);

-- ============================================================
-- FEATURE IMPORTANCE (pré-calculée par modèle)
-- ============================================================
CREATE TABLE IF NOT EXISTS feature_importance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_run_id UUID NOT NULL REFERENCES model_runs(id) ON DELETE CASCADE,
    feature_name TEXT NOT NULL,
    importance FLOAT NOT NULL,
    method TEXT DEFAULT 'shap',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_feature_imp_model ON feature_importance(model_run_id);
CREATE INDEX IF NOT EXISTS idx_feature_imp_name ON feature_importance(feature_name);

-- ============================================================
-- BACKTEST RESULTS
-- ============================================================
CREATE TABLE IF NOT EXISTS backtest_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_run_id UUID NOT NULL REFERENCES model_runs(id) ON DELETE CASCADE,
    asset TEXT NOT NULL DEFAULT 'BTC',
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    initial_capital FLOAT,
    final_capital FLOAT,
    total_return FLOAT,
    sharpe_ratio FLOAT,
    max_drawdown FLOAT,
    win_rate FLOAT,
    n_trades INTEGER,
    metrics JSONB DEFAULT '{}',
    trades JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_backtest_model ON backtest_results(model_run_id);
CREATE INDEX IF NOT EXISTS idx_backtest_asset ON backtest_results(asset);

-- ============================================================
-- RPC: match_documents (pour la recherche vectorielle RAG)
-- ============================================================
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding VECTOR(1536),
    match_count INTEGER DEFAULT 5,
    filter_type TEXT DEFAULT NULL
)
RETURNS TABLE(
    id UUID,
    title TEXT,
    content TEXT,
    doc_type TEXT,
    source TEXT,
    asset TEXT,
    url TEXT,
    tags TEXT[],
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.title,
        d.content,
        d.doc_type,
        d.source,
        d.asset,
        d.url,
        d.tags,
        d.metadata,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM documents d
    WHERE (filter_type IS NULL OR d.doc_type = filter_type)
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================================
-- RPC: match_news (pour la recherche d'actualités par similarité)
-- ============================================================
CREATE OR REPLACE FUNCTION match_news(
    query_embedding VECTOR(1536),
    match_count INTEGER DEFAULT 10,
    filter_type TEXT DEFAULT NULL
)
RETURNS TABLE(
    id UUID,
    title TEXT,
    summary TEXT,
    source TEXT,
    event_type TEXT,
    event_date TIMESTAMPTZ,
    url TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        n.id,
        n.title,
        n.summary,
        n.source,
        n.event_type,
        n.event_date,
        n.url,
        1 - (n.embedding <=> query_embedding) AS similarity
    FROM news_events n
    WHERE (filter_type IS NULL OR n.event_type = filter_type)
    ORDER BY n.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================================
-- TRIGGER: auto-create profile on user signup
-- ============================================================
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO profiles (id, email, full_name)
    VALUES (NEW.id, NEW.email, NEW.raw_user_meta_data->>'full_name');
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ============================================================
-- RLS (Row Level Security)
-- ============================================================
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users can view own conversations" ON conversations FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create own conversations" ON conversations FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete own conversations" ON conversations FOR DELETE USING (auth.uid() = user_id);
CREATE POLICY "Users can view own messages" ON messages FOR SELECT USING (
    EXISTS (SELECT 1 FROM conversations WHERE conversations.id = messages.conversation_id AND conversations.user_id = auth.uid())
);
CREATE POLICY "Users can create own messages" ON messages FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM conversations WHERE conversations.id = messages.conversation_id AND conversations.user_id = auth.uid())
);

-- Documents, news, model_runs, dataset_metadata: accessibles à tous les users authentifiés
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE dataset_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_importance ENABLE ROW LEVEL SECURITY;
ALTER TABLE backtest_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated can read documents" ON documents FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated can read news" ON news_events FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated can read model_runs" ON model_runs FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated can read dataset_metadata" ON dataset_metadata FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated can read feature_importance" ON feature_importance FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated can read backtest_results" ON backtest_results FOR SELECT TO authenticated USING (true);

-- Admin can write
CREATE POLICY "Admin can manage documents" ON documents FOR ALL TO authenticated USING (
    EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.role = 'admin')
);
CREATE POLICY "Admin can manage news" ON news_events FOR ALL TO authenticated USING (
    EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.role = 'admin')
);
CREATE POLICY "Admin can manage model_runs" ON model_runs FOR ALL TO authenticated USING (
    EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.role = 'admin')
);

-- ============ REPORTS ============
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    report_type TEXT NOT NULL DEFAULT 'training',
    status TEXT NOT NULL DEFAULT 'completed',
    content TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Authenticated can read reports" ON reports FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated can create reports" ON reports FOR INSERT TO authenticated USING (true);
