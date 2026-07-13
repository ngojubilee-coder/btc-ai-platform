"""News API routes."""
from fastapi import APIRouter, HTTPException
from services.news_service import refresh_news, search_news_events, correlate_price_movement
from db.supabase_client import get_supabase

router = APIRouter(prefix="/news", tags=["news"])


@router.post("/refresh")
async def refresh():
    try:
        return await refresh_news()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search(start_date: str = None, end_date: str = None, event_type: str = None, limit: int = 20, offset: int = 0):
    try:
        return await search_news_events(start_date, end_date, event_type, limit, offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correlate")
async def correlate(date: str = None, price_change_pct: float = 0.0, limit: int = 10):
    """Get news events correlated with price movements."""
    try:
        if date:
            return await correlate_price_movement(date, price_change_pct)
        sb = get_supabase()
        res = sb.table("news_events").select("*").order("event_date", desc=True).limit(limit).execute()
        if not res.data:
            return []
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
