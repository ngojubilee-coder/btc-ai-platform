"""Client Supabase + helpers DB."""
from supabase import create_client, Client
from core.config import settings

_client: Client | None = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_key or settings.supabase_key)
    return _client


async def fetch_documents_by_type(doc_type: str, limit: int = 100) -> list[dict]:
    sb = get_supabase()
    res = sb.table("documents").select("*").eq("doc_type", doc_type).limit(limit).execute()
    return res.data


async def insert_document(doc: dict) -> dict:
    sb = get_supabase()
    res = sb.table("documents").insert(doc).execute()
    return res.data[0] if res.data else {}


async def search_similar_documents(embedding: list[float], top_k: int = 5, doc_type: str | None = None) -> list[dict]:
    sb = get_supabase()
    params = {"query_embedding": embedding, "match_count": top_k}
    if doc_type:
        params["filter_type"] = doc_type
    res = sb.rpc("match_documents", params).execute()
    return res.data


async def save_message(conversation_id: str, role: str, content: str, llm_model: str = "", tools_called: list = None) -> dict:
    sb = get_supabase()
    res = sb.table("messages").insert({
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "llm_model": llm_model,
        "tools_called": tools_called or [],
    }).execute()
    return res.data[0] if res.data else {}


async def create_conversation(user_id: str, title: str = "New conversation", asset: str = "BTC") -> dict:
    sb = get_supabase()
    res = sb.table("conversations").insert({
        "user_id": user_id,
        "title": title,
        "asset": asset,
    }).execute()
    return res.data[0] if res.data else {}


async def get_conversations(user_id: str, limit: int = 50) -> list[dict]:
    sb = get_supabase()
    res = sb.table("conversations").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
    return res.data


async def get_messages(conversation_id: str) -> list[dict]:
    sb = get_supabase()
    res = sb.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at").execute()
    return res.data


async def delete_conversation(conversation_id: str) -> bool:
    sb = get_supabase()
    sb.table("messages").delete().eq("conversation_id", conversation_id).execute()
    sb.table("conversations").delete().eq("id", conversation_id).execute()
    return True


async def save_report(title: str, report_type: str, status: str = "completed", content: str = "") -> dict:
    sb = get_supabase()
    res = sb.table("reports").insert({
        "title": title,
        "report_type": report_type,
        "status": status,
        "content": content,
    }).execute()
    return res.data[0] if res.data else {}


async def get_reports(limit: int = 20) -> list[dict]:
    sb = get_supabase()
    res = sb.table("reports").select("*").order("created_at", desc=True).limit(limit).execute()
    return res.data
