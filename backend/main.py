"""FastAPI main entry point."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.rate_limit import RateLimitMiddleware
from core.logging_config import logger

from api.auth import router as auth_router
from api.chat import router as chat_router
from api.data import router as data_router
from api.news import router as news_router
from api.models import router as models_router
from api.whales import router as whales_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Index dataset documentation into RAG on startup if available."""
    doc_path = os.path.join(os.path.dirname(__file__), "..", "..", "DATASET_DOCUMENTATION.md")
    if os.path.exists(doc_path):
        try:
            from core.rag import rag_engine
            with open(doc_path, "r", encoding="utf-8") as f:
                content = f.read()
            await rag_engine.index_document(
                title="DATASET_DOCUMENTATION",
                content=content,
                doc_type="documentation",
                source="local",
            )
            logger.info(f"Indexed DATASET_DOCUMENTATION.md ({len(content)} chars)")
        except Exception as e:
            logger.error(f"RAG indexing skipped: {e}")
    else:
        logger.warning(f"DATASET_DOCUMENTATION.md not found at {doc_path}")
    yield


app = FastAPI(
    title="BTC AI Platform API",
    description="Analyste quantitatif IA pour Bitcoin — chatbot, dataset, modèles, actualités",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)

app.include_router(auth_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(data_router, prefix="/api")
app.include_router(news_router, prefix="/api")
app.include_router(models_router, prefix="/api")
app.include_router(whales_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "BTC AI Platform API",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": [
            "/api/auth/verify",
            "/api/auth/me",
            "/api/chat/stream",
            "/api/chat/conversations",
            "/api/data/schema",
            "/api/data/columns",
            "/api/data/stats",
            "/api/data/correlations",
            "/api/data/sample",
            "/api/data/search",
            "/api/data/time-range",
            "/api/news/search",
            "/api/news/refresh",
            "/api/news/correlate",
            "/api/models/",
            "/api/models/compare",
            "/api/models/reports",
            "/api/models/reports/generate",
            "/api/whales/",
            "/api/whales/stats",
            "/api/whales/top",
            "/api/whales/search",
            "/health",
        ],
    }


@app.get("/health")
async def health():
    """Health check with component status."""
    status = {"status": "ok", "components": {}}

    # Check DuckDB / Parquet
    try:
        from db import duckdb_service
        stats = duckdb_service.get_stats()
        status["components"]["duckdb"] = {
            "status": "ok" if stats else "no_data",
            "rows": stats.get("n_rows", 0) if stats else 0,
        }
    except Exception as e:
        status["components"]["duckdb"] = {"status": "error", "error": str(e)}

    # Check Supabase
    try:
        from db.supabase_client import get_supabase
        sb = get_supabase()
        sb.table("profiles").select("id").limit(1).execute()
        status["components"]["supabase"] = {"status": "ok"}
    except Exception as e:
        status["components"]["supabase"] = {"status": "error", "error": str(e)}

    # Check LLM config
    _placeholders = {"your-gemini-key", "your-openai-key", "your-anthropic-key", "your-api-key", "placeholder", ""}
    def _valid_key(k):
        return bool(k) and k not in _placeholders
    status["components"]["llm"] = {
        "gemini": _valid_key(settings.gemini_api_key),
        "anthropic": _valid_key(settings.anthropic_api_key),
        "openai": _valid_key(settings.openai_api_key),
    }

    # Check Whale service
    try:
        from services.whale_service import get_whale_stats
        whale_stats = get_whale_stats()
        status["components"]["whales"] = {
            "status": "ok",
            "total_wallets": whale_stats.get("total_wallets", 0),
        }
    except Exception as e:
        status["components"]["whales"] = {"status": "error", "error": str(e)}

    # Overall status
    all_ok = all(
        v.get("status") == "ok" or (isinstance(v, dict) and v.get("gemini"))
        for v in status["components"].values()
    )
    status["status"] = "ok" if all_ok else "degraded"

    return status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
