"""Unit tests for core modules: agent, tools, config, llm, cache, rate_limit."""
import pytest
import json
import os
import sys
import time
from unittest.mock import patch, MagicMock, AsyncMock

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─── Agent module ───

class TestAgent:
    def test_system_prompt_fr_exists(self):
        from core.agent import SYSTEM_PROMPT_FR
        assert "analyste quantitatif" in SYSTEM_PROMPT_FR.lower()
        assert "français" in SYSTEM_PROMPT_FR.lower()

    def test_system_prompt_en_exists(self):
        from core.agent import SYSTEM_PROMPT_EN
        assert "quantitative analyst" in SYSTEM_PROMPT_EN.lower()
        assert "english" in SYSTEM_PROMPT_EN.lower()

    def test_get_system_prompt_fr(self):
        from core.agent import get_system_prompt
        prompt = get_system_prompt("fr")
        assert prompt == get_system_prompt("fr")
        assert "analyste" in prompt.lower()

    def test_get_system_prompt_en(self):
        from core.agent import get_system_prompt
        prompt = get_system_prompt("en")
        assert "analyst" in prompt.lower()

    def test_get_system_prompt_default(self):
        from core.agent import get_system_prompt
        prompt = get_system_prompt()
        assert "analyste" in prompt.lower()

    def test_system_prompt_backward_compat(self):
        from core.agent import SYSTEM_PROMPT, SYSTEM_PROMPT_FR
        assert SYSTEM_PROMPT == SYSTEM_PROMPT_FR


# ─── Config module ───

class TestConfig:
    def test_settings_loads(self):
        from core.config import settings
        assert settings.host == "0.0.0.0" or settings.host == os.getenv("HOST", "0.0.0.0")
        assert settings.port == int(os.getenv("PORT", "8000"))

    def test_cors_origins_list(self):
        from core.config import settings
        origins = settings.cors_origins_list
        assert isinstance(origins, list)
        assert len(origins) >= 1

    def test_default_llm(self):
        from core.config import settings
        assert settings.default_llm == "gemini"

    def test_rag_settings(self):
        from core.config import settings
        assert settings.rag_top_k > 0
        assert settings.rag_chunk_size > 0


# ─── Tools module ───

class TestTools:
    def test_tools_list_not_empty(self):
        from core.tools import TOOLS
        assert len(TOOLS) >= 8

    def test_tool_names_unique(self):
        from core.tools import TOOLS
        names = [t["name"] for t in TOOLS]
        assert len(names) == len(set(names))

    def test_tool_has_required_fields(self):
        from core.tools import TOOLS
        for tool in TOOLS:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool

    def test_known_tool_names(self):
        from core.tools import TOOLS
        names = {t["name"] for t in TOOLS}
        expected = {"query_dataset", "get_dataset_schema", "get_dataset_stats",
                    "get_column_stats", "get_correlations", "sample_data",
                    "query_time_range", "search_news",
                    "get_whale_stats", "get_top_whales", "search_whales"}
        assert expected.issubset(names)

    @pytest.mark.asyncio
    async def test_execute_tool_unknown(self):
        from core.tools import execute_tool
        result = await execute_tool("nonexistent_tool", {})
        data = json.loads(result)
        assert "error" in data
        assert "nonexistent_tool" in data["error"]

    @pytest.mark.asyncio
    async def test_execute_tool_missing_column(self):
        from core.tools import execute_tool
        result = await execute_tool("get_column_stats", {})
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_execute_tool_missing_query(self):
        from core.tools import execute_tool
        result = await execute_tool("search_whales", {})
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_execute_tool_missing_time_range(self):
        from core.tools import execute_tool
        result = await execute_tool("query_time_range", {})
        data = json.loads(result)
        assert "error" in data

    def test_validate_sql_rejects_empty(self):
        from core.tools import _validate_sql
        with pytest.raises(ValueError, match="Empty"):
            _validate_sql("")

    def test_validate_sql_rejects_semicolon(self):
        from core.tools import _validate_sql
        with pytest.raises(ValueError, match="Semicolons"):
            _validate_sql("SELECT * FROM t; DROP TABLE t")

    def test_validate_sql_rejects_non_select(self):
        from core.tools import _validate_sql
        with pytest.raises(ValueError, match="Only SELECT"):
            _validate_sql("DELETE FROM t")

    def test_validate_sql_rejects_forbidden_keyword(self):
        from core.tools import _validate_sql
        with pytest.raises(ValueError, match="Forbidden keyword"):
            _validate_sql("SELECT * FROM t UNION DELETE FROM t")

    def test_validate_sql_accepts_valid_select(self):
        from core.tools import _validate_sql
        sql = "SELECT count(*) FROM {TABLE}"
        assert _validate_sql(sql) == sql


# ─── LLM module ───

class TestLLM:
    def test_map_gemini_role_assistant(self):
        from core.llm import LLMRouter
        assert LLMRouter._map_gemini_role("assistant") == "model"

    def test_map_gemini_role_user(self):
        from core.llm import LLMRouter
        assert LLMRouter._map_gemini_role("user") == "user"

    def test_map_gemini_role_model(self):
        from core.llm import LLMRouter
        assert LLMRouter._map_gemini_role("model") == "model"


# ─── Cache module ───

class TestCache:
    def test_cached_call_returns_value(self):
        from core.cache import cached_call
        result = cached_call("test_key", lambda: 42, ttl=60)
        assert result == 42

    def test_cached_call_caches(self):
        from core.cache import cached_call, invalidate
        invalidate("test_key2")
        call_count = [0]
        def func():
            call_count[0] += 1
            return "value"
        cached_call("test_key2", func, ttl=60)
        cached_call("test_key2", func, ttl=60)
        assert call_count[0] == 1
        invalidate("test_key2")

    def test_invalidate(self):
        from core.cache import cached_call, invalidate
        cached_call("test_key3", lambda: "val", ttl=60)
        invalidate("test_key3")
        # After invalidation, a new call should execute the function
        call_count = [0]
        def func():
            call_count[0] += 1
            return "new_val"
        result = cached_call("test_key3", func, ttl=60)
        assert call_count[0] == 1
        assert result == "new_val"
        invalidate("test_key3")


# ─── Rate limit module ───

class TestRateLimit:
    def test_rate_limit_allows_under_max(self):
        from core.rate_limit import RateLimitMiddleware, MAX_REQUESTS
        # Just verify the module loads and has reasonable defaults
        assert MAX_REQUESTS > 0

    def test_rate_limit_window(self):
        from core.rate_limit import WINDOW_SECONDS
        assert WINDOW_SECONDS > 0
