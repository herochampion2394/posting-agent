from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.models import KnowledgeDoc, User
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge Base"])

class KnowledgeCreate(BaseModel):
    title: str
    content: str
    source_url: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[list] = None

async def get_authenticated_user(db: Session, authorization: str = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = get_current_user(authorization)
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/")
async def list_knowledge(authorization: str = Header(None), db: Session = Depends(get_db)):
    user = await get_authenticated_user(db, authorization)
    docs = db.query(KnowledgeDoc).filter(KnowledgeDoc.user_id == user.id, KnowledgeDoc.is_active == True).all()
    
    return [
        {
            "id": doc.id,
            "title": doc.title,
            "content": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
            "category": doc.category,
            "keywords": doc.keywords,
            "created_at": doc.created_at.isoformat()
        }
        for doc in docs
    ]

@router.post("/")
async def create_knowledge(doc_data: KnowledgeCreate, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = await get_authenticated_user(db, authorization)
    
    new_doc = KnowledgeDoc(
        user_id=user.id,
        title=doc_data.title,
        content=doc_data.content,
        source_url=doc_data.source_url,
        category=doc_data.category,
        keywords=doc_data.keywords or []
    )
    
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    
    return {"id": new_doc.id, "message": "Knowledge document created successfully"}

@router.delete("/{doc_id}")
async def delete_knowledge(doc_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = await get_authenticated_user(db, authorization)
    
    doc = db.query(KnowledgeDoc).filter(KnowledgeDoc.id == doc_id, KnowledgeDoc.user_id == user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db.delete(doc)
    db.commit()
    
    return {"message": "Document deleted successfully"}
