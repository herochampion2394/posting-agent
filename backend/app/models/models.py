from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    social_accounts = relationship("SocialAccount", back_populates="user")
    posts = relationship("Post", back_populates="user")
    schedules = relationship("Schedule", back_populates="user")
    knowledge_docs = relationship("KnowledgeDoc", back_populates="user")

class SocialPlatform(str, enum.Enum):
    TWITTER = "twitter"
    TIKTOK = "tiktok"

class SocialAccount(Base):
    __tablename__ = "social_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    platform = Column(Enum(SocialPlatform), nullable=False)
    platform_user_id = Column(String)
    platform_username = Column(String)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="social_accounts")
    posts = relationship("Post", back_populates="social_account")

class PostStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    POSTED = "posted"
    FAILED = "failed"

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    social_account_id = Column(Integer, ForeignKey("social_accounts.id"))
    content = Column(Text, nullable=False)
    media_urls = Column(JSON)  # List of media URLs
    platform = Column(Enum(SocialPlatform), nullable=False)
    status = Column(Enum(PostStatus), default=PostStatus.DRAFT)
    scheduled_at = Column(DateTime)
    posted_at = Column(DateTime)
    platform_post_id = Column(String)  # ID from Twitter/TikTok
    platform_post_url = Column(String)
    error_message = Column(Text)
    ai_generated = Column(Boolean, default=False)
    generation_prompt = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="posts")
    social_account = relationship("SocialAccount", back_populates="posts")

class FrequencyType(str, enum.Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"

class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    platform = Column(Enum(SocialPlatform), nullable=False)
    frequency_type = Column(Enum(FrequencyType), nullable=False)
    frequency_value = Column(Integer)  # e.g., 3 for "3 times per day"
    time_slots = Column(JSON)  # List of time slots like ["09:00", "13:00", "18:00"]
    is_active = Column(Boolean, default=True)
    use_trending_data = Column(Boolean, default=True)
    use_knowledge_base = Column(Boolean, default=True)
    content_template = Column(Text)
    last_run = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="schedules")

class KnowledgeDoc(Base):
    __tablename__ = "knowledge_docs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(String)
    file_url = Column(String)
    category = Column(String)
    keywords = Column(JSON)  # List of keywords for context matching
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="knowledge_docs")

class TrendingTopic(Base):
    __tablename__ = "trending_topics"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String)  # "twitter", "google", "reddit", etc.
    topic = Column(String, nullable=False)
    description = Column(Text)
    url = Column(String)
    volume = Column(Integer)  # Trend volume/engagement
    scraped_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # When this trend data becomes stale
