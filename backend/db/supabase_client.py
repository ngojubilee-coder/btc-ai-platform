"""Database client — SQLite implementation (replaces Supabase)."""
import json
from db.sqlite_db import get_db, init_db, _uuid, _row_to_dict

# Initialize DB on import
init_db()


class _TableQuery:
    """Mimics Supabase table query builder for backward compatibility."""

    def __init__(self, table: str):
        self._table = table
        self._wheres = []
        self._order_by = None
        self._order_desc = False
        self._limit_val = None
        self._offset_val = None

    def eq(self, col: str, val):
        self._wheres.append((col, "=", val))
        return self

    def neq(self, col: str, val):
        self._wheres.append((col, "!=", val))
        return self

    def gte(self, col: str, val):
        self._wheres.append((col, ">=", val))
        return self

    def lte(self, col: str, val):
        self._wheres.append((col, "<=", val))
        return self

    def ilike(self, col: str, val):
        self._wheres.append((col, "LIKE", val))
        return self

    def order(self, col: str, desc=False):
        self._order_by = col
        self._order_desc = desc
        return self

    def limit(self, n: int):
        self._limit_val = n
        return self

    def range(self, start: int, end: int):
        self._limit_val = end - start + 1
        self._offset_val = start
        return self

    def execute(self):
        db = get_db()
        sql = f"SELECT * FROM {self._table}"
        params = []
        if self._wheres:
            clauses = []
            for col, op, val in self._wheres:
                clauses.append(f"{col} {op} ?")
                params.append(val)
            sql += " WHERE " + " AND ".join(clauses)
        if self._order_by:
            sql += f" ORDER BY {self._order_by} {'DESC' if self._order_desc else 'ASC'}"
        if self._limit_val:
            sql += f" LIMIT {self._limit_val}"
        if self._offset_val:
            sql += f" OFFSET {self._offset_val}"
        rows = db.execute(sql, params).fetchall()
        return _Result([_row_to_dict(r) for r in rows])


class _Result:
    def __init__(self, data):
        self.data = data


class _InsertQuery:
    def __init__(self, table: str, data: dict):
        self._table = table
        self._data = data

    def execute(self):
        db = get_db()
        row = {}
        for k, v in self._data.items():
            if isinstance(v, (list, dict)):
                row[k] = json.dumps(v)
            elif v is None:
                row[k] = None
            else:
                row[k] = v
        if "id" not in row or not row["id"]:
            row["id"] = _uuid()
        cols = list(row.keys())
        placeholders = ", ".join(["?"] * len(cols))
        sql = f"INSERT INTO {self._table} ({', '.join(cols)}) VALUES ({placeholders})"
        db.execute(sql, list(row.values()))
        db.commit()
        fetched = db.execute(f"SELECT * FROM {self._table} WHERE id = ?", [row["id"]]).fetchone()
        return _Result([_row_to_dict(fetched)] if fetched else [])


class _DeleteQuery:
    def __init__(self, table: str):
        self._table = table
        self._wheres = []

    def eq(self, col: str, val):
        self._wheres.append((col, "=", val))
        return self

    def execute(self):
        db = get_db()
        sql = f"DELETE FROM {self._table}"
        params = []
        if self._wheres:
            clauses = []
            for col, op, val in self._wheres:
                clauses.append(f"{col} {op} ?")
                params.append(val)
            sql += " WHERE " + " AND ".join(clauses)
        db.execute(sql, params)
        db.commit()
        return _Result([])


class _UpdateQuery:
    def __init__(self, table: str, data: dict):
        self._table = table
        self._data = data
        self._wheres = []

    def eq(self, col: str, val):
        self._wheres.append((col, "=", val))
        return self

    def execute(self):
        db = get_db()
        sets = []
        params = []
        for k, v in self._data.items():
            if isinstance(v, (list, dict)):
                sets.append(f"{k} = ?")
                params.append(json.dumps(v))
            else:
                sets.append(f"{k} = ?")
                params.append(v)
        sql = f"UPDATE {self._table} SET " + ", ".join(sets)
        if self._wheres:
            clauses = []
            for col, op, val in self._wheres:
                clauses.append(f"{col} {op} ?")
                params.append(val)
            sql += " WHERE " + " AND ".join(clauses)
        db.execute(sql, params)
        db.commit()
        return _Result([])


class _DBClient:
    """Mimics Supabase client API for backward compatibility."""

    def table(self, name: str):
        class _Table:
            def select(self, *args):
                return _TableQuery(name)

            def insert(self, data: dict):
                return _InsertQuery(name, data)

            def delete(self):
                return _DeleteQuery(name)

            def update(self, data: dict):
                return _UpdateQuery(name, data)

        return _Table()

    def rpc(self, fn_name: str, params: dict):
        return _Result([])


_client = _DBClient()


def get_supabase() -> _DBClient:
    """Return the DB client (SQLite backend, Supabase-compatible API)."""
    return _client


# ─── Async helpers (same API as before) ───

async def fetch_documents_by_type(doc_type: str, limit: int = 100) -> list[dict]:
    db = get_db()
    rows = db.execute(
        "SELECT * FROM documents WHERE doc_type = ? ORDER BY created_at DESC LIMIT ?",
        [doc_type, limit],
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


async def insert_document(doc: dict) -> dict:
    db = get_db()
    row = {}
    for k, v in doc.items():
        if isinstance(v, (list, dict)):
            row[k] = json.dumps(v)
        else:
            row[k] = v
    if "id" not in row or not row["id"]:
        row["id"] = _uuid()
    cols = list(row.keys())
    placeholders = ", ".join(["?"] * len(cols))
    db.execute(f"INSERT INTO documents ({', '.join(cols)}) VALUES ({placeholders})", list(row.values()))
    db.commit()
    fetched = db.execute("SELECT * FROM documents WHERE id = ?", [row["id"]]).fetchone()
    return _row_to_dict(fetched) or {}


async def search_similar_documents(embedding: list[float], top_k: int = 5, doc_type: str | None = None) -> list[dict]:
    db = get_db()
    if doc_type:
        rows = db.execute(
            "SELECT * FROM documents WHERE doc_type = ? ORDER BY created_at DESC LIMIT ?",
            [doc_type, top_k],
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM documents ORDER BY created_at DESC LIMIT ?",
            [top_k],
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


async def save_message(conversation_id: str, role: str, content: str, llm_model: str = "", tools_called: list = None) -> dict:
    db = get_db()
    msg_id = _uuid()
    db.execute(
        "INSERT INTO messages (id, conversation_id, role, content, llm_model, tools_called) VALUES (?, ?, ?, ?, ?, ?)",
        [msg_id, conversation_id, role, content, llm_model, json.dumps(tools_called or [])],
    )
    db.commit()
    fetched = db.execute("SELECT * FROM messages WHERE id = ?", [msg_id]).fetchone()
    return _row_to_dict(fetched) or {}


async def create_conversation(user_id: str, title: str = "New conversation", asset: str = "BTC") -> dict:
    db = get_db()
    conv_id = _uuid()
    db.execute(
        "INSERT INTO conversations (id, user_id, title, asset) VALUES (?, ?, ?, ?)",
        [conv_id, user_id, title, asset],
    )
    db.commit()
    fetched = db.execute("SELECT * FROM conversations WHERE id = ?", [conv_id]).fetchone()
    return _row_to_dict(fetched) or {}


async def get_conversations(user_id: str, limit: int = 50) -> list[dict]:
    db = get_db()
    rows = db.execute(
        "SELECT * FROM conversations WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        [user_id, limit],
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


async def get_messages(conversation_id: str) -> list[dict]:
    db = get_db()
    rows = db.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        [conversation_id],
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


async def delete_conversation(conversation_id: str) -> bool:
    db = get_db()
    db.execute("DELETE FROM messages WHERE conversation_id = ?", [conversation_id])
    db.execute("DELETE FROM conversations WHERE id = ?", [conversation_id])
    db.commit()
    return True


async def save_report(title: str, report_type: str, status: str = "completed", content: str = "") -> dict:
    db = get_db()
    report_id = _uuid()
    db.execute(
        "INSERT INTO reports (id, title, report_type, status, content) VALUES (?, ?, ?, ?, ?)",
        [report_id, title, report_type, status, content],
    )
    db.commit()
    fetched = db.execute("SELECT * FROM reports WHERE id = ?", [report_id]).fetchone()
    return _row_to_dict(fetched) or {}


async def get_reports(limit: int = 20) -> list[dict]:
    db = get_db()
    rows = db.execute(
        "SELECT * FROM reports ORDER BY created_at DESC LIMIT ?",
        [limit],
    ).fetchall()
    return [_row_to_dict(r) for r in rows]
