"""Whale tracking API routes."""
from fastapi import APIRouter, HTTPException
from services.whale_service import (
    get_all_wallets,
    get_wallet_by_address,
    get_whale_stats,
    get_top_whales,
    search_wallets,
)

router = APIRouter(prefix="/whales", tags=["whales"])


@router.get("/")
async def list_wallets(
    category: str | None = None,
    entity: str | None = None,
    min_btc: float | None = None,
    limit: int = 100,
    offset: int = 0,
):
    """List known whale wallets with optional filters."""
    try:
        return get_all_wallets(category, entity, min_btc, limit, offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def whale_stats():
    """Aggregate statistics about known whale wallets."""
    try:
        return get_whale_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top")
async def top_whales(limit: int = 20):
    """Top whale wallets by estimated BTC holdings."""
    try:
        return get_top_whales(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search(q: str, limit: int = 20, offset: int = 0):
    """Search wallets by address, name, or entity."""
    try:
        return search_wallets(q, limit, offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{address}")
async def wallet_detail(address: str):
    """Get details for a specific wallet address."""
    try:
        wallet = get_wallet_by_address(address)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        return wallet
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
