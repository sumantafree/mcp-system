"""YouTube MCP — scripts, titles, Shorts, descriptions."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.database import get_db
from database import models
from core.dependencies import get_current_user
from agents.youtube_agent import YouTubeAgent
from datetime import datetime
from typing import Optional, List

router = APIRouter(prefix="/youtube", tags=["YouTube MCP"])


class ScriptRequest(BaseModel):
    topic: str
    duration_minutes: int = 10
    style: str = "educational"
    language: str = "en"


class TitleRequest(BaseModel):
    topic: str
    niche: str


class ShortsRequest(BaseModel):
    main_script: str
    topic: str


class DescriptionRequest(BaseModel):
    title: str
    script_summary: str
    keywords: List[str] = []


class AuditRequest(BaseModel):
    channel_data: dict


class VideoSaveRequest(BaseModel):
    title: str
    description: Optional[str] = None
    script: Optional[str] = None
    tags: List[str] = []
    status: str = "draft"


@router.post("/script/generate")
async def generate_script(
    data: ScriptRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = YouTubeAgent(db, current_user.id)
    result = await agent.generate_script(data.topic, data.duration_minutes, data.style, data.language)

    # Save video record
    video = models.YouTubeVideo(
        title=result.get("title_options", [data.topic])[0],
        script=result.get("hook", "") + "\n\n" + str(result.get("sections", "")),
        ai_title_suggestions=result.get("title_options", []),
        tags=result.get("key_points", []),
        status="draft",
        owner_id=current_user.id,
    )
    db.add(video)
    db.commit()

    return {**result, "video_id": video.id}


@router.post("/title/optimize")
async def optimize_title(
    data: TitleRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = YouTubeAgent(db, current_user.id)
    return await agent.optimize_title(data.topic, data.niche)


@router.post("/shorts/generate")
async def generate_shorts(
    data: ShortsRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = YouTubeAgent(db, current_user.id)
    return await agent.generate_shorts_script(data.main_script, data.topic)


@router.post("/description/generate")
async def generate_description(
    data: DescriptionRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = YouTubeAgent(db, current_user.id)
    description = await agent.generate_description(data.title, data.script_summary, data.keywords)
    return {"description": description}


@router.post("/channel/audit")
async def audit_channel(
    data: AuditRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = YouTubeAgent(db, current_user.id)
    return await agent.channel_audit(data.channel_data)


@router.get("/videos")
def list_videos(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.YouTubeVideo).filter_by(owner_id=current_user.id)
    if status:
        query = query.filter_by(status=status)
    return query.order_by(models.YouTubeVideo.created_at.desc()).limit(50).all()


@router.get("/videos/{video_id}")
def get_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    video = db.query(models.YouTubeVideo).filter_by(id=video_id, owner_id=current_user.id).first()
    if not video:
        raise HTTPException(404, "Video not found")
    return video


@router.post("/videos/save", status_code=201)
def save_video(
    data: VideoSaveRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    video = models.YouTubeVideo(
        title=data.title,
        description=data.description,
        script=data.script,
        tags=data.tags,
        status=data.status,
        owner_id=current_user.id,
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


@router.delete("/videos/{video_id}")
def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    video = db.query(models.YouTubeVideo).filter_by(id=video_id, owner_id=current_user.id).first()
    if not video:
        raise HTTPException(404, "Video not found")
    db.delete(video)
    db.commit()
    return {"deleted": True}
