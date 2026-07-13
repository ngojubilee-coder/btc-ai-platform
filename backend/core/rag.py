"""RAG Engine — Retrieval-Augmented Generation with pgvector."""
from core.embeddings import embedding_service
from core.config import settings
from db.supabase_client import get_supabase, search_similar_documents


class RAGEngine:
    def __init__(self):
        self.top_k = settings.rag_top_k

    async def retrieve(self, query: str, doc_type: str | None = None, top_k: int | None = None) -> list[dict]:
        embedding = embedding_service.embed(query)
        k = top_k or self.top_k
        docs = await search_similar_documents(embedding, k, doc_type)
        return docs

    async def retrieve_and_format(self, query: str, doc_type: str | None = None) -> str:
        docs = await self.retrieve(query, doc_type)
        if not docs:
            return ""
        parts = []
        for i, doc in enumerate(docs, 1):
            title = doc.get("title", "Untitled")
            content = doc.get("content", "")[:2000]
            source = doc.get("source", "unknown")
            parts.append(f"[{i}] {title} (source: {source})\n{content}")
        return "\n\n---\n\n".join(parts)

    async def index_document(self, title: str, content: str, doc_type: str, source: str = "", asset: str = "BTC", url: str = "", tags: list[str] = None) -> dict:
        embedding = embedding_service.embed(content[:8000])
        from db.supabase_client import insert_document
        return await insert_document({
            "title": title,
            "content": content,
            "doc_type": doc_type,
            "source": source,
            "asset": asset,
            "url": url,
            "tags": tags or [],
            "embedding": embedding,
        })

    async def index_news(self, title: str, summary: str, content: str, source: str, event_type: str, event_date: str, sentiment: float = 0.0, url: str = "") -> dict:
        text = f"{title}. {summary}. {content[:2000]}"
        embedding = embedding_service.embed(text)
        sb = get_supabase()
        res = sb.table("news_events").insert({
            "title": title,
            "summary": summary,
            "content": content,
            "source": source,
            "event_type": event_type,
            "sentiment": sentiment,
            "url": url,
            "event_date": event_date,
            "embedding": embedding,
        }).execute()
        return res.data[0] if res.data else {}


rag_engine = RAGEngine()
