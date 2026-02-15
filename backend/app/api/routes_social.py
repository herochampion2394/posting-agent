from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.models import SocialAccount, User, SocialPlatform
from app.services.auth import get_current_user
from app.integrations.twitter import get_twitter_oauth_url, handle_twitter_callback
from app.integrations.tiktok import get_tiktok_oauth_url, exchange_tiktok_code

router = APIRouter(prefix="/api/social", tags=["Social Accounts"])

class TwitterCallback(BaseModel):
    oauth_token: str
    oauth_verifier: str

class TikTokCallback(BaseModel):
    code: str

async def get_authenticated_user(db: Session, authorization: str = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = get_current_user(authorization)
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/")
async def list_accounts(authorization: str = Header(None), db: Session = Depends(get_db)):
    user = await get_authenticated_user(db, authorization)
    accounts = db.query(SocialAccount).filter(SocialAccount.user_id == user.id).all()
    
    return [
        {
            "id": acc.id,
            "platform": acc.platform.value,
            "platform_username": acc.platform_username,
            "is_active": acc.is_active,
            "created_at": acc.created_at.isoformat()
        }
        for acc in accounts
    ]

@router.get("/twitter/auth-url")
async def get_twitter_auth():
    url = get_twitter_oauth_url()
    return {"auth_url": url}

@router.post("/twitter/callback")
async def twitter_callback(callback: TwitterCallback, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = await get_authenticated_user(db, authorization)
    
    result = handle_twitter_callback(callback.oauth_token, callback.oauth_verifier)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Create or update social account
    account = db.query(SocialAccount).filter(
        SocialAccount.user_id == user.id,
        SocialAccount.platform == SocialPlatform.TWITTER
    ).first()
    
    if account:
        account.access_token = result["access_token"]
        account.refresh_token = result["access_token_secret"]
    else:
        account = SocialAccount(
            user_id=user.id,
            platform=SocialPlatform.TWITTER,
            access_token=result["access_token"],
            refresh_token=result["access_token_secret"]
        )
        db.add(account)
    
    db.commit()
    return {"message": "Twitter account connected successfully"}

@router.get("/tiktok/auth-url")
async def get_tiktok_auth():
    url = get_tiktok_oauth_url()
    return {"auth_url": url}

@router.post("/tiktok/callback")
async def tiktok_callback(callback: TikTokCallback, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = await get_authenticated_user(db, authorization)
    
    result = await exchange_tiktok_code(callback.code)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    account = db.query(SocialAccount).filter(
        SocialAccount.user_id == user.id,
        SocialAccount.platform == SocialPlatform.TIKTOK
    ).first()
    
    if account:
        account.access_token = result["access_token"]
        account.refresh_token = result["refresh_token"]
    else:
        account = SocialAccount(
            user_id=user.id,
            platform=SocialPlatform.TIKTOK,
            access_token=result["access_token"],
            refresh_token=result["refresh_token"]
        )
        db.add(account)
    
    db.commit()
    return {"message": "TikTok account connected successfully"}

@router.delete("/{account_id}")
async def disconnect_account(account_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = await get_authenticated_user(db, authorization)
    
    account = db.query(SocialAccount).filter(SocialAccount.id == account_id, SocialAccount.user_id == user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    db.delete(account)
    db.commit()
    
    return {"message": "Account disconnected successfully"}
