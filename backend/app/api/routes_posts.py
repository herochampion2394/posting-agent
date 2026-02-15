from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.models import Post, PostStatus, SocialPlatform, User
from app.services.auth import get_current_user
from app.services.ai_generator import AIContentGenerator

router = APIRouter(prefix="/api/posts", tags=["Posts"])

class PostCreate(BaseModel):
    content: str
    platform: str
    social_account_id: int
    scheduled_at: Optional[str] = None

class PostUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[str] = None

class AIGenerateRequest(BaseModel):
    platform: str
    use_knowledge_base: bool = True
    use_trending: bool = True
    custom_prompt: Optional[str] = None
    tone: str = "professional"

async def get_authenticated_user(db: Session, authorization: str = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = get_current_user(authorization)
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/")
async def list_posts(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 50
):
    user = await get_authenticated_user(db, authorization)
    
    query = db.query(Post).filter(Post.user_id == user.id)
    
    if status:
        query = query.filter(Post.status == status)
    if platform:
        query = query.filter(Post.platform == platform)
    
    posts = query.order_by(Post.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": p.id,
            "content": p.content,
            "platform": p.platform.value,
            "status": p.status.value,
            "scheduled_at": p.scheduled_at.isoformat() if p.scheduled_at else None,
            "posted_at": p.posted_at.isoformat() if p.posted_at else None,
            "platform_post_url": p.platform_post_url,
            "ai_generated": p.ai_generated,
            "created_at": p.created_at.isoformat()
        }
        for p in posts
    ]

@router.post("/")
async def create_post(
    post_data: PostCreate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = await get_authenticated_user(db, authorization)
    
    new_post = Post(
        user_id=user.id,
        social_account_id=post_data.social_account_id,
        content=post_data.content,
        platform=SocialPlatform(post_data.platform),
        status=PostStatus.SCHEDULED if post_data.scheduled_at else PostStatus.DRAFT,
        scheduled_at=datetime.fromisoformat(post_data.scheduled_at) if post_data.scheduled_at else None
    )
    
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    return {"id": new_post.id, "message": "Post created successfully"}

@router.post("/generate")
async def generate_post(
    request: AIGenerateRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = await get_authenticated_user(db, authorization)
    
    ai_gen = AIContentGenerator()
    
    knowledge_base = []
    if request.use_knowledge_base:
        from app.models.models import KnowledgeDoc
        kb_docs = db.query(KnowledgeDoc).filter(
            KnowledgeDoc.user_id == user.id,
            KnowledgeDoc.is_active == True
        ).limit(3).all()
        knowledge_base = [doc.content for doc in kb_docs]
    
    trending_topics = []
    if request.use_trending:
        from app.services.scraper import WebScraper
        scraper = WebScraper()
        trends = await scraper.get_trending_topics()
        trending_topics = [f"{t['topic']}: {t['description']}" for t in trends[:3]]
    
    content = await ai_gen.generate_post(
        platform=request.platform,
        knowledge_base=knowledge_base,
        trending_topics=trending_topics,
        custom_prompt=request.custom_prompt,
        tone=request.tone
    )
    
    return {"content": content, "platform": request.platform}

@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = await get_authenticated_user(db, authorization)
    
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    db.delete(post)
    db.commit()
    
    return {"message": "Post deleted successfully"}
