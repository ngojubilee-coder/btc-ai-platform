"""Unit tests for services: whale_service, news_service, reports."""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─── Whale Service ───

class TestWhaleService:
    def test_get_whale_stats(self):
        from services.whale_service import get_whale_stats
        stats = get_whale_stats()
        assert "total_wallets" in stats
        assert "total_btc" in stats
        assert "categories" in stats
        assert isinstance(stats["total_wallets"], int)
        assert stats["total_wallets"] > 0

    def test_get_top_whales(self):
        from services.whale_service import get_top_whales
        whales = get_top_whales(limit=5)
        assert isinstance(whales, list)
        assert len(whales) <= 5
        if whales:
            assert "address" in whales[0]
            assert "name" in whales[0]
            assert "estimated_btc" in whales[0]

    def test_get_top_whales_sorted_desc(self):
        from services.whale_service import get_top_whales
        whales = get_top_whales(limit=10)
        btcs = [w.get("estimated_btc") or 0 for w in whales]
        assert btcs == sorted(btcs, reverse=True)

    def test_search_wallets_by_name(self):
        from services.whale_service import search_wallets
        results = search_wallets("binance", limit=5)
        assert isinstance(results, list)
        if results:
            r = results[0].get("name", "").lower()
            e = results[0].get("entity", "").lower()
            assert "binance" in r or "binance" in e

    def test_search_wallets_empty_query(self):
        from services.whale_service import search_wallets
        results = search_wallets("", limit=5)
        assert isinstance(results, list)

    def test_get_all_wallets_with_category(self):
        from services.whale_service import get_all_wallets
        wallets = get_all_wallets(category="EXCHANGE", limit=10)
        assert isinstance(wallets, list)
        for w in wallets:
            assert w["category"].upper() == "EXCHANGE"

    def test_get_all_wallets_with_min_btc(self):
        from services.whale_service import get_all_wallets
        wallets = get_all_wallets(min_btc=1000, limit=10)
        for w in wallets:
            assert (w.get("estimated_btc") or 0) >= 1000

    def test_get_wallet_by_address_not_found(self):
        from services.whale_service import get_wallet_by_address
        result = get_wallet_by_address("1FakeAddress12345")
        assert result is None

    def test_safe_float(self):
        from services.whale_service import _safe_float
        assert _safe_float("123.45") == 123.45
        assert _safe_float(None) is None
        assert _safe_float("") is None
        assert _safe_float("abc") is None
        assert _safe_float("0") == 0.0


# ─── News Service ───

class TestNewsService:
    @pytest.mark.asyncio
    async def test_search_news_events(self):
        from services.news_service import search_news_events
        with patch("services.news_service.get_supabase") as mock_sb:
            mock_chain = mock_sb.return_value.table.return_value.select.return_value
            mock_chain.order.return_value.range.return_value.execute.return_value = MagicMock(data=[])
            results = await search_news_events(None, None, None, 5)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_news_with_type(self):
        from services.news_service import search_news_events
        with patch("services.news_service.get_supabase") as mock_sb:
            mock_chain = mock_sb.return_value.table.return_value.select.return_value.eq.return_value
            mock_chain.order.return_value.range.return_value.execute.return_value = MagicMock(data=[])
            results = await search_news_events(None, None, "fed", 5)
        assert isinstance(results, list)


# ─── Reports Service ───

class TestReportsService:
    def test_reports_module_imports(self):
        try:
            from services import reports
            assert hasattr(reports, '__file__')
        except ImportError:
            pytest.skip("reports module has external dependencies")
