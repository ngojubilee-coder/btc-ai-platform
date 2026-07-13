"""Auth routes — JWT verification + user management."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from core.config import settings
from db.supabase_client import get_supabase
import jwt

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenVerify(BaseModel):
    token: str


async def get_current_user(token: str = Depends(lambda r: r.headers.get("Authorization", "").replace("Bearer ", ""))) -> dict:
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/verify")
async def verify_token(body: TokenVerify):
    try:
        payload = jwt.decode(body.token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        sb = get_supabase()
        profile = sb.table("profiles").select("*").eq("id", payload["sub"]).execute()
        return {"valid": True, "user": profile.data[0] if profile.data else None}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    sb = get_supabase()
    profile = sb.table("profiles").select("*").eq("id", user["sub"]).execute()
    return profile.data[0] if profile.data else {"id": user["sub"], "email": user.get("email")}
