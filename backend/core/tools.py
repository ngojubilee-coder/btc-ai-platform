"""Function definitions for LLM tool calling."""
import json
from db import duckdb_service


TOOLS = [
    {
        "name": "query_dataset",
        "description": "Execute a SQL query on the BTC dataset (Parquet via DuckDB). Use {TABLE} as the table name placeholder. Returns rows as JSON.",
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "SQL query. Use {TABLE} for the dataset table."},
                "limit": {"type": "integer", "description": "Max rows to return", "default": 100}
            },
            "required": ["sql"]
        }
    },
    {
        "name": "get_dataset_schema",
        "description": "Get the schema (column names and types) of the BTC dataset.",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "get_dataset_stats",
        "description": "Get basic statistics about the dataset (row count, column count, file size, date range).",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "get_column_stats",
        "description": "Get statistics (min, max, mean, std, null count) for a specific column.",
        "parameters": {
            "type": "object",
            "properties": {"column": {"type": "string", "description": "Column name"}},
            "required": ["column"]
        }
    },
    {
        "name": "get_correlations",
        "description": "Get top correlations between features and a target column.",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target column name", "default": "target_return_15m"},
                "top_n": {"type": "integer", "description": "Number of top correlations", "default": 20}
            }
        }
    },
    {
        "name": "sample_data",
        "description": "Get a random sample of rows from the dataset.",
        "parameters": {
            "type": "object",
            "properties": {"n": {"type": "integer", "description": "Number of rows", "default": 100}}
        }
    },
    {
        "name": "query_time_range",
        "description": "Query data within a specific time range.",
        "parameters": {
            "type": "object",
            "properties": {
                "start": {"type": "string", "description": "Start datetime (ISO format)"},
                "end": {"type": "string", "description": "End datetime (ISO format)"},
                "columns": {"type": "array", "items": {"type": "string"}, "description": "Columns to select"},
                "limit": {"type": "integer", "description": "Max rows", "default": 1000}
            },
            "required": ["start", "end"]
        }
    },
    {
        "name": "search_news",
        "description": "Search news events by date range and/or event type. Returns correlated news for market movements.",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Start date (ISO)"},
                "end_date": {"type": "string", "description": "End date (ISO)"},
                "event_type": {"type": "string", "description": "fed, cpi, rate, etf, halving, liquidation, hack, regulation, market, whale, mining"},
                "limit": {"type": "integer", "default": 20}
            }
        }
    },
    {
        "name": "get_whale_stats",
        "description": "Get aggregate statistics about known whale wallets (total wallets, total BTC, categories, top entities).",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "get_top_whales",
        "description": "Get top whale wallets by estimated BTC holdings. Returns address, name, entity, category, and estimated BTC.",
        "parameters": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "description": "Number of top whales", "default": 20}}
        }
    },
    {
        "name": "search_whales",
        "description": "Search whale wallets by address, name, or entity name.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (address, name, or entity)"},
                "limit": {"type": "integer", "default": 20}
            },
            "required": ["query"]
        }
    }
]


def _validate_sql(sql: str) -> str:
    """Validate SQL query for safety: only SELECT, no forbidden keywords, no semicolons."""
    import re
    if not sql or not sql.strip():
        raise ValueError("Empty SQL query")
    if ";" in sql:
        raise ValueError("Semicolons are not allowed")
    sql_stripped = sql.strip().lower()
    if not sql_stripped.startswith("select"):
        raise ValueError("Only SELECT queries are allowed")
    forbidden = ["insert", "update", "delete", "drop", "alter", "create", "truncate", "attach", "detach", "copy", "export", "import", "pragma", "vacuum"]
    for kw in forbidden:
        if re.search(rf"\b{kw}\b", sql_stripped):
            raise ValueError(f"Forbidden keyword: {kw}")
    return sql


async def execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool and return the result as a string."""
    try:
        if name == "query_dataset":
            sql = _validate_sql(arguments.get("sql", ""))
            limit = arguments.get("limit", 100)
            rows = duckdb_service.query(sql)
            rows = rows[:limit]
            return json.dumps(rows, default=str, ensure_ascii=False)

        elif name == "get_dataset_schema":
            return json.dumps(duckdb_service.get_schema(), ensure_ascii=False)

        elif name == "get_dataset_stats":
            return json.dumps(duckdb_service.get_stats(), ensure_ascii=False)

        elif name == "get_column_stats":
            col = arguments.get("column")
            if not col:
                return json.dumps({"error": "Missing required argument: column"})
            return json.dumps(duckdb_service.get_column_stats(col), ensure_ascii=False)

        elif name == "get_correlations":
            return json.dumps(duckdb_service.get_correlations(
                arguments.get("target", "target_return_15m"),
                arguments.get("top_n", 20)
            ), ensure_ascii=False)

        elif name == "sample_data":
            return json.dumps(duckdb_service.sample_data(arguments.get("n", 100)), default=str, ensure_ascii=False)

        elif name == "query_time_range":
            start = arguments.get("start")
            end = arguments.get("end")
            if not start or not end:
                return json.dumps({"error": "Missing required arguments: start and end"})
            return json.dumps(duckdb_service.query_time_range(
                start, end,
                arguments.get("columns"), arguments.get("limit", 1000)
            ), default=str, ensure_ascii=False)

        elif name == "search_news":
            from services.news_service import search_news_events
            return json.dumps(await search_news_events(
                arguments.get("start_date"), arguments.get("end_date"),
                arguments.get("event_type"), arguments.get("limit", 20)
            ), default=str, ensure_ascii=False)

        elif name == "get_whale_stats":
            from services.whale_service import get_whale_stats
            return json.dumps(get_whale_stats(), ensure_ascii=False)

        elif name == "get_top_whales":
            from services.whale_service import get_top_whales
            return json.dumps(get_top_whales(arguments.get("limit", 20)), ensure_ascii=False)

        elif name == "search_whales":
            from services.whale_service import search_wallets
            query = arguments.get("query")
            if not query:
                return json.dumps({"error": "Missing required argument: query"})
            return json.dumps(search_wallets(query, arguments.get("limit", 20)), ensure_ascii=False)

        else:
            return json.dumps({"error": f"Unknown tool: {name}"})

    except Exception as e:
        return json.dumps({"error": str(e)})
