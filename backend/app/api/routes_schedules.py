from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app.models.models import Schedule, User, FrequencyType, SocialPlatform
from app.services.auth import get_current_user
from app.services.scheduler import post_scheduler

router = APIRouter(prefix="/api/schedules", tags=["Schedules"])

class ScheduleCreate(BaseModel):
    name: str
    platform: str
    frequency_type: str
    frequency_value: Optional[int] = None
    time_slots: List[str]
    use_trending_data: bool = True
    use_knowledge_base: bool = True
    content_template: Optional[str] = None

async def get_authenticated_user(db: Session, authorization: str = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = get_current_user(authorization)
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/")
async def list_schedules(authorization: str = Header(None), db: Session = Depends(get_db)):
    user = await get_authenticated_user(db, authorization)
    schedules = db.query(Schedule).filter(Schedule.user_id == user.id).all()
    
    return [
        {
            "id": s.id,
            "name": s.name,
            "platform": s.platform.value,
            "frequency_type": s.frequency_type.value,
            "frequency_value": s.frequency_value,
            "time_slots": s.time_slots,
            "is_active": s.is_active,
            "last_run": s.last_run.isoformat() if s.last_run else None,
            "created_at": s.created_at.isoformat()
        }
        for s in schedules
    ]

@router.post("/")
async def create_schedule(schedule_data: ScheduleCreate, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = await get_authenticated_user(db, authorization)
    
    new_schedule = Schedule(
        user_id=user.id,
        name=schedule_data.name,
        platform=SocialPlatform(schedule_data.platform),
        frequency_type=FrequencyType(schedule_data.frequency_type),
        frequency_value=schedule_data.frequency_value,
        time_slots=schedule_data.time_slots,
        use_trending_data=schedule_data.use_trending_data,
        use_knowledge_base=schedule_data.use_knowledge_base,
        content_template=schedule_data.content_template,
        is_active=True
    )
    
    db.add(new_schedule)
    db.commit()
    db.refresh(new_schedule)
    
    post_scheduler.add_schedule(new_schedule.id, user.id)
    
    return {"id": new_schedule.id, "message": "Schedule created successfully"}

@router.put("/{schedule_id}/toggle")
async def toggle_schedule(schedule_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = await get_authenticated_user(db, authorization)
    
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.user_id == user.id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule.is_active = not schedule.is_active
    db.commit()
    
    if schedule.is_active:
        post_scheduler.add_schedule(schedule.id, user.id)
    else:
        post_scheduler.remove_schedule(schedule.id)
    
    return {"is_active": schedule.is_active}

@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = await get_authenticated_user(db, authorization)
    
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.user_id == user.id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    post_scheduler.remove_schedule(schedule.id)
    db.delete(schedule)
    db.commit()
    
    return {"message": "Schedule deleted successfully"}
