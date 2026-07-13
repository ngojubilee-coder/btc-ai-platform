"""Configuration centrale du backend BTC AI Platform."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")

    # LLM
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "")
    redis_token: str = os.getenv("REDIS_TOKEN", "")

    # News
    cryptocompare_api_key: str = os.getenv("CRYPTOCOMPARE_API_KEY", "")
    newsapi_key: str = os.getenv("NEWSAPI_KEY", "")

    # Data
    data_dir: str = os.getenv("DATA_DIR", str(BASE_DIR / "data"))
    parquet_path: str = os.getenv("PARQUET_PATH", str(BASE_DIR / "data" / "btc_enriched_dataset_1m.parquet"))

    # Auth
    jwt_secret: str = os.getenv("JWT_SECRET", "change-this-secret")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expire_hours: int = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")

    # LLM defaults
    default_llm: str = "gemini"
    fallback_llm: str = "claude"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 3072

    # RAG
    rag_top_k: int = 5
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
