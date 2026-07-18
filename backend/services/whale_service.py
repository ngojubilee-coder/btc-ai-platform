"""Whale tracking service — known whale wallets, transactions, and patterns."""
import csv
import os
from pathlib import Path
from typing import Optional
from core.logging_config import logger

WHALE_CSV_PATH = os.getenv(
    "WHALE_WALLETS_CSV",
    str(Path(__file__).resolve().parent.parent.parent / "data" / "whale_wallets_list.csv"),
)

_wallets_cache: list[dict] | None = None


def _load_wallets() -> list[dict]:
    """Load whale wallets from CSV file."""
    global _wallets_cache
    if _wallets_cache is not None:
        return _wallets_cache

    wallets: list[dict] = []
    p = Path(WHALE_CSV_PATH)
    if not p.exists():
        logger.warning(f"[WhaleService] CSV not found: {p}")
        return wallets

    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            wallets.append({
                "address": row.get("address", ""),
                "category": row.get("category", ""),
                "name": row.get("name", ""),
                "entity": row.get("entity", ""),
                "type": row.get("type", ""),
                "estimated_btc": _safe_float(row.get("estimated_btc")),
                "source": row.get("source", ""),
            })

    _wallets_cache = wallets
    logger.info(f"[WhaleService] Loaded {len(wallets)} whale wallets from {p}")
    return wallets


def _safe_float(val: str | None) -> float | None:
    if not val:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def get_all_wallets(
    category: str | None = None,
    entity: str | None = None,
    min_btc: float | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """Get whale wallets with optional filters."""
    wallets = _load_wallets()

    filtered = wallets
    if category:
        filtered = [w for w in filtered if w["category"].upper() == category.upper()]
    if entity:
        filtered = [w for w in filtered if w["entity"].upper() == entity.upper()]
    if min_btc is not None:
        filtered = [w for w in filtered if w["estimated_btc"] and w["estimated_btc"] >= min_btc]

    filtered = sorted(filtered, key=lambda w: w.get("estimated_btc") or 0, reverse=True)
    return filtered[offset:offset + limit]


def get_wallet_by_address(address: str) -> dict | None:
    """Get a specific wallet by its address."""
    wallets = _load_wallets()
    for w in wallets:
        if w["address"].lower() == address.lower():
            return w
    return None


def get_whale_stats() -> dict:
    """Aggregate statistics about known whale wallets."""
    wallets = _load_wallets()
    if not wallets:
        return {"total_wallets": 0, "total_btc": 0, "categories": {}, "entities": {}}

    total_btc = sum(w.get("estimated_btc") or 0 for w in wallets)
    categories: dict[str, int] = {}
    entities: dict[str, int] = {}

    for w in wallets:
        cat = w.get("category", "UNKNOWN")
        categories[cat] = categories.get(cat, 0) + 1
        ent = w.get("entity", "Unknown")
        entities[ent] = entities.get(ent, 0) + 1

    return {
        "total_wallets": len(wallets),
        "total_btc": round(total_btc, 2),
        "categories": categories,
        "top_entities": dict(sorted(entities.items(), key=lambda x: x[1], reverse=True)[:10]),
    }


def get_top_whales(limit: int = 20) -> list[dict]:
    """Get top whale wallets by estimated BTC holdings."""
    wallets = _load_wallets()
    sorted_wallets = sorted(wallets, key=lambda w: w.get("estimated_btc") or 0, reverse=True)
    return sorted_wallets[:limit]


def search_wallets(query: str, limit: int = 20, offset: int = 0) -> list[dict]:
    """Search wallets by address, name, or entity."""
    wallets = _load_wallets()
    q = query.lower()
    results = [
        w for w in wallets
        if q in w.get("address", "").lower()
        or q in w.get("name", "").lower()
        or q in w.get("entity", "").lower()
    ]
    return results[offset:offset + limit]
