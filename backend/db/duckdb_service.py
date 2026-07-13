"""DuckDB service — query Parquet files without loading into RAM."""
import duckdb
import pandas as pd
from pathlib import Path
from core.config import settings
from typing import Any

_conn: duckdb.DuckDBPyConnection | None = None


def get_connection() -> duckdb.DuckDBPyConnection:
    global _conn
    if _conn is None:
        _conn = duckdb.connect(":memory:")
        _conn.execute("INSTALL parquet; LOAD parquet;")
    return _conn


def _parquet_path() -> str:
    p = Path(settings.parquet_path)
    if not p.exists():
        raise FileNotFoundError(f"Parquet file not found: {p}")
    return str(p)


def query(sql: str) -> list[dict]:
    """Execute arbitrary SQL on the Parquet dataset."""
    conn = get_connection()
    path = _parquet_path()
    full_sql = sql.replace("{TABLE}", f"read_parquet('{path}')")
    result = conn.execute(full_sql).fetchdf()
    return result.to_dict(orient="records")


def get_schema() -> dict:
    """Return column names and types."""
    conn = get_connection()
    path = _parquet_path()
    df = conn.execute(f"DESCRIBE SELECT * FROM read_parquet('{path}')").fetchdf()
    return {
        "columns": [
            {"name": row["column_name"], "type": row["column_type"]}
            for _, row in df.iterrows()
        ]
    }


def get_stats() -> dict:
    """Pre-computed basic statistics."""
    conn = get_connection()
    path = _parquet_path()

    n_rows = conn.execute(f"SELECT COUNT(*) FROM read_parquet('{path}')").fetchone()[0]
    schema_df = conn.execute(f"DESCRIBE SELECT * FROM read_parquet('{path}')").fetchdf()
    n_cols = len(schema_df)

    min_ts = max_ts = None
    if "timestamp" in schema_df["column_name"].values:
        ts_result = conn.execute(f"SELECT MIN(timestamp), MAX(timestamp) FROM read_parquet('{path}')").fetchone()
        min_ts = str(ts_result[0]) if ts_result[0] else None
        max_ts = str(ts_result[1]) if ts_result[1] else None

    return {
        "n_rows": n_rows,
        "n_columns": n_cols,
        "file_size_mb": round(Path(path).stat().st_size / 1024 / 1024, 1),
        "min_timestamp": min_ts,
        "max_timestamp": max_ts,
    }


def get_column_stats(column: str) -> dict:
    """Statistics for a specific column."""
    import re
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", column):
        raise ValueError(f"Invalid column name: {column}")
    conn = get_connection()
    path = _parquet_path()
    df = conn.execute(f"""
        SELECT
            MIN("{column}") as min_val,
            MAX("{column}") as max_val,
            AVG("{column}") as mean_val,
            STDDEV("{column}") as std_val,
            COUNT("{column}") as count_val,
            COUNT(*) - COUNT("{column}") as null_count
        FROM read_parquet('{path}')
    """).fetchdf()
    row = df.iloc[0]
    return {
        "column": column,
        "min": float(row["min_val"]) if pd.notna(row["min_val"]) else None,
        "max": float(row["max_val"]) if pd.notna(row["max_val"]) else None,
        "mean": float(row["mean_val"]) if pd.notna(row["mean_val"]) else None,
        "std": float(row["std_val"]) if pd.notna(row["std_val"]) else None,
        "count": int(row["count_val"]),
        "null_count": int(row["null_count"]),
    }


def get_correlations(target: str = "target_return_15m", top_n: int = 20) -> list[dict]:
    """Top correlations with a target column."""
    import re
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", target):
        raise ValueError(f"Invalid target column: {target}")
    top_n = max(1, min(int(top_n), 100))
    conn = get_connection()
    path = _parquet_path()
    schema = conn.execute(f"DESCRIBE SELECT * FROM read_parquet('{path}')").fetchdf()
    numeric_cols = [r["column_name"] for _, r in schema.iterrows() if "FLOAT" in r["column_type"].upper() or "DOUBLE" in r["column_type"].upper()]
    all_cols = [r["column_name"] for _, r in schema.iterrows()]
    if target not in all_cols:
        raise ValueError(f"Target column '{target}' not found in dataset")
    numeric_cols = [c for c in numeric_cols if c != target and not c.startswith("target_")]
    if not numeric_cols:
        return []

    cols_sql = ", ".join([f'"{c}"' for c in numeric_cols + [target]])
    df = conn.execute(f"""
        SELECT {cols_sql}
        FROM read_parquet('{path}')
        USING SAMPLE 10 PERCENT
    """).fetchdf()

    corrs = df[numeric_cols].corrwith(df[target]).abs().sort_values(ascending=False).head(top_n)
    return [{"feature": col, "correlation": float(corrs[col])} for col in corrs.index]


def sample_data(n: int = 100, offset: int = 0) -> list[dict]:
    """Sample of n rows with offset for pagination."""
    n = max(1, min(int(n), 10000))
    offset = max(0, int(offset))
    conn = get_connection()
    path = _parquet_path()
    if offset > 0:
        df = conn.execute(f"""
            SELECT * FROM read_parquet('{path}')
            LIMIT {n} OFFSET {offset}
        """).fetchdf()
    else:
        df = conn.execute(f"""
            SELECT * FROM read_parquet('{path}')
            USING SAMPLE {n} ROWS
        """).fetchdf()
    return df.to_dict(orient="records")


def query_time_range(start: str, end: str, columns: list[str] | None = None, limit: int = 1000) -> list[dict]:
    """Query data within a time range."""
    import re
    limit = max(1, min(int(limit), 50000))
    if not re.match(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?$", start):
        raise ValueError(f"Invalid start date: {start}")
    if not re.match(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?$", end):
        raise ValueError(f"Invalid end date: {end}")
    if columns:
        for c in columns:
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", c):
                raise ValueError(f"Invalid column name: {c}")
    conn = get_connection()
    path = _parquet_path()
    col_sql = ", ".join([f'"{c}"' for c in columns]) if columns else "*"
    df = conn.execute(f"""
        SELECT {col_sql}
        FROM read_parquet('{path}')
        WHERE timestamp >= '{start}' AND timestamp <= '{end}'
        LIMIT {limit}
    """).fetchdf()
    return df.to_dict(orient="records")
