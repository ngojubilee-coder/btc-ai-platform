"""Unit tests for API endpoints using FastAPI TestClient."""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


# ─── Health & root ───

class TestHealthRoot:
    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data
        assert "endpoints" in data
        assert isinstance(data["endpoints"], list)

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "components" in data


# ─── Data API ───

class TestDataAPI:
    def test_get_schema(self, client):
        resp = client.get("/api/data/schema")
        assert resp.status_code in (200, 500)  # 500 if no parquet

    def test_get_stats(self, client):
        resp = client.get("/api/data/stats")
        assert resp.status_code in (200, 500)

    def test_get_columns(self, client):
        resp = client.get("/api/data/columns")
        assert resp.status_code in (200, 500)

    def test_get_correlations(self, client):
        resp = client.get("/api/data/correlations?top_n=5")
        assert resp.status_code in (200, 500)

    def test_sample_data(self, client):
        resp = client.get("/api/data/sample?n=5")
        assert resp.status_code in (200, 500)

    def test_query_empty_sql(self, client):
        resp = client.get("/api/data/query?sql=")
        assert resp.status_code == 400

    def test_query_non_select(self, client):
        resp = client.get("/api/data/query?sql=DROP TABLE x")
        assert resp.status_code == 400

    def test_query_with_semicolon(self, client):
        resp = client.get("/api/data/query?sql=SELECT 1; DROP TABLE x")
        assert resp.status_code == 400

    def test_query_forbidden_keyword(self, client):
        resp = client.get("/api/data/query?sql=SELECT * FROM t WHERE 1=1 AND INSERT INTO")
        assert resp.status_code == 400

    def test_post_query_empty(self, client):
        resp = client.post("/api/data/query", json={"sql": ""})
        assert resp.status_code == 400

    def test_search_invalid_column(self, client):
        resp = client.get("/api/data/search?column=1bad&value=test")
        assert resp.status_code == 400


# ─── Chat API ───

class TestChatAPI:
    def test_list_conversations(self, client):
        resp = client.get("/api/chat/conversations/test-user")
        assert resp.status_code in (200, 500)

    def test_list_messages(self, client):
        resp = client.get("/api/chat/messages/fake-id")
        assert resp.status_code in (200, 500)

    def test_create_conversation(self, client):
        resp = client.post("/api/chat/conversations", json={"user_id": "test", "title": "Test"})
        assert resp.status_code in (200, 500)

    def test_delete_conversation(self, client):
        resp = client.delete("/api/chat/conversations/fake-id")
        assert resp.status_code in (200, 500)

    def test_execute_tool_no_name(self, client):
        resp = client.post("/api/chat/execute-tool", json={})
        assert resp.status_code == 400

    def test_execute_tool_unknown(self, client):
        resp = client.post("/api/chat/execute-tool", json={"name": "fake_tool"})
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data["result"]


# ─── News API ───

class TestNewsAPI:
    def test_search_news(self, client):
        resp = client.get("/api/news/search?limit=5")
        assert resp.status_code in (200, 500)

    def test_correlate(self, client):
        resp = client.get("/api/news/correlate?limit=5")
        assert resp.status_code in (200, 500)


# ─── Models API ───

class TestModelsAPI:
    def test_list_models(self, client):
        resp = client.get("/api/models/")
        assert resp.status_code in (200, 500)

    def test_list_reports(self, client):
        resp = client.get("/api/models/reports")
        assert resp.status_code in (200, 500)

    def test_get_report_not_found(self, client):
        resp = client.get("/api/models/reports/fake-id-12345")
        assert resp.status_code in (404, 500)

    def test_download_report_not_found(self, client):
        resp = client.get("/api/models/reports/fake-id-12345/download")
        assert resp.status_code == 200  # Returns markdown error message
        assert "not found" in resp.text.lower() or "error" in resp.text.lower()


# ─── Whales API ───

class TestWhalesAPI:
    def test_whale_stats(self, client):
        resp = client.get("/api/whales/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_wallets" in data

    def test_top_whales(self, client):
        resp = client.get("/api/whales/top?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_search_whales(self, client):
        resp = client.get("/api/whales/search?q=binance&limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_list_whales(self, client):
        resp = client.get("/api/whales/?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


# ─── Training API ───

class TestTrainingAPI:
    def test_training_status(self, client):
        resp = client.get("/api/training/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "dataset" in data
        assert "models" in data
        assert "results" in data
        assert "exists" in data["dataset"]
        assert "count" in data["models"]

    def test_training_results(self, client):
        resp = client.get("/api/training/results")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "total" in data
        assert isinstance(data["results"], list)

    def test_training_results_limit(self, client):
        resp = client.get("/api/training/results?limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] <= 2

    def test_training_models(self, client):
        resp = client.get("/api/training/models")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert "total" in data
        assert isinstance(data["models"], list)

    def test_training_comparisons(self, client):
        resp = client.get("/api/training/comparisons")
        assert resp.status_code == 200
        data = resp.json()
        assert "comparisons" in data
        assert "total" in data

    def test_training_result_not_found(self, client):
        resp = client.get("/api/training/results/nonexistent_file.json")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data
