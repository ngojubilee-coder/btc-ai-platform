"""Data API routes — query dataset, schema, stats, correlations."""
from fastapi import APIRouter, HTTPException
from db import duckdb_service
from core.cache import cached_call, invalidate

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/schema")
async def get_schema():
    try:
        return cached_call("schema", duckdb_service.get_schema, ttl=120)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/columns")
async def get_columns():
    """Lightweight column list (names only, no types)."""
    try:
        schema = cached_call("schema", duckdb_service.get_schema, ttl=120)
        return [c["name"] for c in schema.get("columns", [])]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    try:
        return cached_call("stats", duckdb_service.get_stats, ttl=60)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/column/{column}/stats")
async def get_column_stats(column: str):
    try:
        return cached_call(f"colstats:{column}", lambda: duckdb_service.get_column_stats(column), ttl=60)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correlations")
async def get_correlations(target: str = "target_return_15m", top_n: int = 20):
    try:
        return cached_call(f"corr:{target}:{top_n}", lambda: duckdb_service.get_correlations(target, top_n), ttl=120)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sample")
async def sample_data(n: int = 100, offset: int = 0):
    try:
        n = max(1, min(int(n), 10000))
        offset = max(0, int(offset))
        return duckdb_service.sample_data(n, offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/time-range")
async def time_range_data(start: str, end: str, columns: str | None = None, limit: int = 1000):
    """Query data within a time range. Columns is comma-separated."""
    try:
        limit = max(1, min(int(limit), 10000))
        cols = columns.split(",") if columns else None
        return duckdb_service.query_time_range(start, end, cols, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query")
async def query_data_get(sql: str, limit: int = 100):
    try:
        if not sql:
            raise HTTPException(status_code=400, detail="No SQL provided")
        if ";" in sql:
            raise HTTPException(status_code=400, detail="Semicolons are not allowed")
        sql_stripped = sql.strip().lower()
        if not sql_stripped.startswith("select"):
            raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")
        import re as _re
        forbidden = ["insert", "update", "delete", "drop", "alter", "create", "truncate", "attach", "detach", "copy", "export", "import", "pragma", "vacuum"]
        for kw in forbidden:
            if _re.search(rf"\b{kw}\b", sql_stripped):
                raise HTTPException(status_code=400, detail=f"Forbidden keyword: {kw}")
        rows = duckdb_service.query(sql)
        return {"rows": rows[:limit], "total": len(rows)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def query_data(body: dict):
    try:
        sql = body.get("sql", "")
        limit = body.get("limit", 100)
        if not sql:
            raise HTTPException(status_code=400, detail="No SQL provided")
        if ";" in sql:
            raise HTTPException(status_code=400, detail="Semicolons are not allowed")
        sql_stripped = sql.strip().lower()
        if not sql_stripped.startswith("select"):
            raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")
        import re as _re
        forbidden = ["insert", "update", "delete", "drop", "alter", "create", "truncate", "attach", "detach", "copy", "export", "import", "pragma", "vacuum"]
        for kw in forbidden:
            if _re.search(rf"\b{kw}\b", sql_stripped):
                raise HTTPException(status_code=400, detail=f"Forbidden keyword: {kw}")
        rows = duckdb_service.query(sql)
        return {"rows": rows[:limit], "total": len(rows)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_data(column: str, value: str, limit: int = 50, offset: int = 0):
    """Search dataset rows where column contains value (safe, parameterized)."""
    try:
        import re
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", column):
            raise HTTPException(status_code=400, detail="Invalid column name")
        limit = max(1, min(int(limit), 1000))
        offset = max(0, int(offset))
        path = duckdb_service._parquet_path()
        sql = f"""SELECT * FROM read_parquet('{path}') WHERE "{column}"::TEXT ILIKE ? LIMIT {limit} OFFSET {offset}"""
        conn = duckdb_service.get_connection()
        result = conn.execute(sql, [f"%{value}%"]).fetchdf()
        return result.to_dict(orient="records")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/invalidate")
async def invalidate_cache(key: str | None = None):
    """Invalidate cache. If key is provided, invalidate only that key; otherwise clear all."""
    try:
        invalidate(key)
        return {"invalidated": key or "all"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

