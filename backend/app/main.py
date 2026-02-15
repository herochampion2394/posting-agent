from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api import routes_auth, routes_posts, routes_schedules, routes_knowledge, routes_social
from app.services.scheduler import post_scheduler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Posting Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_auth.router)
app.include_router(routes_posts.router)
app.include_router(routes_schedules.router)
app.include_router(routes_knowledge.router)
app.include_router(routes_social.router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Posting Agent API")
    post_scheduler.start()
    logger.info("Scheduler started")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Posting Agent API")
    post_scheduler.shutdown()

@app.get("/")
async def root():
    return {"message": "Posting Agent API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
