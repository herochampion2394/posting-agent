from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import Schedule, Post, PostStatus, SocialAccount, User
from app.services.ai_generator import AIContentGenerator
from app.services.scraper import WebScraper
from app.integrations.twitter import TwitterClient
from app.integrations.tiktok import TikTokClient
from app.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

class PostScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.ai_generator = AIContentGenerator()
        self.scraper = WebScraper()
    
    def start(self):
        """Start the scheduler."""
        self.scheduler.start()
        logger.info("Scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    def add_schedule(self, schedule_id: int, user_id: int):
        """
        Add a schedule to the scheduler.
        """
        db = SessionLocal()
        try:
            schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
            if not schedule or not schedule.is_active:
                return
            
            # Parse time slots and create cron triggers
            if schedule.time_slots:
                for time_slot in schedule.time_slots:
                    hour, minute = map(int, time_slot.split(":"))
                    
                    # Create cron trigger based on frequency type
                    if schedule.frequency_type == "daily":
                        trigger = CronTrigger(hour=hour, minute=minute)
                    elif schedule.frequency_type == "weekly":
                        # Default to Monday, can be made configurable
                        trigger = CronTrigger(day_of_week="mon", hour=hour, minute=minute)
                    elif schedule.frequency_type == "hourly":
                        trigger = CronTrigger(minute=minute)
                    else:
                        continue
                    
                    # Add job to scheduler
                    job_id = f"schedule_{schedule_id}_{time_slot}"
                    self.scheduler.add_job(
                        self._execute_scheduled_post,
                        trigger=trigger,
                        args=[schedule_id, user_id],
                        id=job_id,
                        replace_existing=True
                    )
                    
                    logger.info(f"Added job {job_id} for user {user_id}")
        finally:
            db.close()
    
    def remove_schedule(self, schedule_id: int):
        """Remove a schedule from the scheduler."""
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            if job.id.startswith(f"schedule_{schedule_id}_"):
                self.scheduler.remove_job(job.id)
                logger.info(f"Removed job {job.id}")
    
    async def _execute_scheduled_post(self, schedule_id: int, user_id: int):
        """
        Execute a scheduled post - generate content and post to platform.
        """
        db = SessionLocal()
        try:
            schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
            if not schedule or not schedule.is_active:
                return
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return
            
            # Get social account for this platform
            social_account = db.query(SocialAccount).filter(
                SocialAccount.user_id == user_id,
                SocialAccount.platform == schedule.platform,
                SocialAccount.is_active == True
            ).first()
            
            if not social_account:
                logger.error(f"No active social account for user {user_id} on {schedule.platform}")
                return
            
            # Gather context for content generation
            knowledge_base = []
            if schedule.use_knowledge_base:
                kb_docs = db.query(KnowledgeDoc).filter(
                    KnowledgeDoc.user_id == user_id,
                    KnowledgeDoc.is_active == True
                ).limit(3).all()
                knowledge_base = [doc.content for doc in kb_docs]
            
            trending_topics = []
            if schedule.use_trending_data:
                trends = await self.scraper.get_trending_topics()
                trending_topics = [f"{t['topic']}: {t['description']}" for t in trends[:3]]
            
            # Generate content
            content = await self.ai_generator.generate_post(
                platform=schedule.platform.value,
                knowledge_base=knowledge_base,
                trending_topics=trending_topics,
                custom_prompt=schedule.content_template
            )
            
            # Create post record
            post = Post(
                user_id=user_id,
                social_account_id=social_account.id,
                content=content,
                platform=schedule.platform,
                status=PostStatus.SCHEDULED,
                ai_generated=True,
                generation_prompt=f"Auto-generated from schedule {schedule.name}",
                scheduled_at=datetime.utcnow()
            )
            db.add(post)
            db.commit()
            db.refresh(post)
            
            # Post to platform
            await self._post_to_platform(post, social_account, db)
            
            # Update schedule last_run
            schedule.last_run = datetime.utcnow()
            db.commit()
            
            logger.info(f"Successfully executed scheduled post {post.id} for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to execute scheduled post: {e}")
        finally:
            db.close()
    
    async def _post_to_platform(self, post: Post, social_account: SocialAccount, db: Session):
        """
        Post content to the appropriate platform.
        """
        try:
            if post.platform.value == "twitter":
                client = TwitterClient(
                    access_token=social_account.access_token,
                    access_token_secret=social_account.refresh_token  # Using refresh_token field for token_secret
                )
                result = await client.post_tweet(post.content)
                
                if result.get("success"):
                    post.status = PostStatus.POSTED
                    post.posted_at = datetime.utcnow()
                    post.platform_post_id = result["tweet_id"]
                    post.platform_post_url = result["tweet_url"]
                else:
                    post.status = PostStatus.FAILED
                    post.error_message = result.get("error", "Unknown error")
            
            elif post.platform.value == "tiktok":
                client = TikTokClient(access_token=social_account.access_token)
                # For TikTok, we'd need video content, so this is a placeholder
                # In a real implementation, you'd generate or select video content
                post.status = PostStatus.FAILED
                post.error_message = "TikTok video posting requires video content"
            
            db.commit()
        except Exception as e:
            post.status = PostStatus.FAILED
            post.error_message = str(e)
            db.commit()
            logger.error(f"Failed to post to {post.platform}: {e}")

# Global scheduler instance
post_scheduler = PostScheduler()
