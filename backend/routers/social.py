"""Social Media MCP — scheduling, post generation, calendar."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.database import get_db
from database import models
from core.dependencies import get_current_user
from agents.social_agent import SocialAgent
from datetime import datetime
from typing import Optional, List

router = APIRouter(prefix="/social", tags=["Social Media MCP"])


class GeneratePostRequest(BaseModel):
    topic: str
    platform: str = "instagram"
    language: str = "en"


class SchedulePostRequest(BaseModel):
    platform: str
    caption: str
    hashtags: List[str] = []
    media_urls: List[str] = []
    scheduled_at: datetime


class HashtagRequest(BaseModel):
    niche: str
    platform: str = "instagram"


class CalendarRequest(BaseModel):
    niche: str
    platforms: List[str]
    days: int = 7


class PerformanceRequest(BaseModel):
    caption: str
    metrics: dict


@router.post("/generate")
async def generate_post(
    data: GeneratePostRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = SocialAgent(db, current_user.id)
    return await agent.generate_post(data.topic, data.platform, data.language)


@router.post("/schedule", status_code=201)
def schedule_post(
    data: SchedulePostRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    post = models.SocialPost(
        platform=data.platform,
        caption=data.caption,
        hashtags=data.hashtags,
        media_urls=data.media_urls,
        scheduled_at=data.scheduled_at,
        status="scheduled",
        owner_id=current_user.id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return {"id": post.id, "scheduled_at": post.scheduled_at, "status": post.status}


@router.get("/posts")
def list_posts(
    platform: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(30, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.SocialPost).filter_by(owner_id=current_user.id)
    if platform:
        query = query.filter_by(platform=platform)
    if status:
        query = query.filter_by(status=status)
    posts = query.order_by(models.SocialPost.created_at.desc()).limit(limit).all()
    return posts


@router.get("/posts/{post_id}")
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    post = db.query(models.SocialPost).filter_by(id=post_id, owner_id=current_user.id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    return post


@router.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    post = db.query(models.SocialPost).filter_by(id=post_id, owner_id=current_user.id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    db.delete(post)
    db.commit()
    return {"deleted": True}


@router.post("/hashtags")
async def get_hashtags(
    data: HashtagRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = SocialAgent(db, current_user.id)
    return await agent.get_trending_hashtags(data.niche, data.platform)


@router.post("/calendar")
async def generate_calendar(
    data: CalendarRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = SocialAgent(db, current_user.id)
    return await agent.generate_content_calendar(data.niche, data.platforms, data.days)


@router.post("/analyze")
async def analyze_performance(
    data: PerformanceRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = SocialAgent(db, current_user.id)
    return await agent.analyze_post_performance(data.caption, data.metrics)


@router.get("/optimal-times/{platform}")
def optimal_times(
    platform: str,
    count: int = Query(3, le=7),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = SocialAgent(db, current_user.id)
    return agent.get_optimal_schedule(platform, count)


@router.get("/accounts")
def list_accounts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    accounts = db.query(models.SocialAccount).filter_by(owner_id=current_user.id, is_active=True).all()
    return accounts
