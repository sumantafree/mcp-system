"""Content MCP — blog generation, news rewriting, social captions."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.database import get_db
from database import models
from core.dependencies import get_current_user
from agents.content_agent import ContentAgent
from slugify import slugify
from datetime import datetime
from typing import Optional, List

router = APIRouter(prefix="/content", tags=["Content MCP"])


class BlogGenerateRequest(BaseModel):
    topic: str
    keyword: str
    language: str = "en"
    word_count: int = 1200
    tone: str = "professional"


class NewsRewriteRequest(BaseModel):
    original_text: str
    language: str = "en"
    style: str = "news"


class CaptionRequest(BaseModel):
    topic: str
    platform: str = "instagram"
    language: str = "en"
    count: int = 3


class TranslateRequest(BaseModel):
    content: str
    target_language: str


class ContentUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


@router.post("/blog/generate", status_code=201)
async def generate_blog(
    data: BlogGenerateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = ContentAgent(db, current_user.id)
    result = await agent.generate_blog(
        data.topic, data.keyword, data.language, data.word_count, data.tone
    )

    # Save to DB
    slug = result.get("slug") or slugify(data.topic)
    # Ensure unique slug
    existing = db.query(models.ContentPost).filter_by(slug=slug).first()
    if existing:
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

    post = models.ContentPost(
        title=result.get("title", data.topic),
        slug=slug,
        content=result.get("content"),
        excerpt=result.get("excerpt"),
        content_type="blog",
        language=data.language,
        target_keyword=data.keyword,
        word_count=result.get("estimated_word_count"),
        tags=result.get("tags", []),
        meta={"meta_title": result.get("meta_title"), "meta_description": result.get("meta_description")},
        ai_model_used="gemini-1.5-flash",
        prompt_used=f"Blog: {data.topic} | Keyword: {data.keyword}",
        status=models.ContentStatus.draft,
        owner_id=current_user.id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    return {**result, "post_id": post.id, "saved": True}


@router.post("/news/rewrite")
async def rewrite_news(
    data: NewsRewriteRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = ContentAgent(db, current_user.id)
    result = await agent.rewrite_news(data.original_text, data.language, data.style)

    # Save to DB
    post = models.ContentPost(
        title=result.get("title", "Rewritten Article"),
        slug=f"news-{int(datetime.utcnow().timestamp())}",
        content=result.get("rewritten_content"),
        excerpt=result.get("summary"),
        content_type="news",
        language=data.language,
        status=models.ContentStatus.draft,
        owner_id=current_user.id,
    )
    db.add(post)
    db.commit()

    return {**result, "post_id": post.id}


@router.post("/captions/generate")
async def generate_captions(
    data: CaptionRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = ContentAgent(db, current_user.id)
    return await agent.generate_social_captions(data.topic, data.platform, data.language, data.count)


@router.post("/translate")
async def translate_content(
    data: TranslateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = ContentAgent(db, current_user.id)
    translated = await agent.translate_content(data.content, data.target_language)
    return {"translated_content": translated, "target_language": data.target_language}


@router.get("/posts")
def list_posts(
    content_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.ContentPost).filter_by(owner_id=current_user.id)
    if content_type:
        query = query.filter_by(content_type=content_type)
    if status:
        query = query.filter_by(status=status)
    if language:
        query = query.filter_by(language=language)
    if search:
        query = query.filter(models.ContentPost.title.ilike(f"%{search}%"))

    total = query.count()
    posts = query.order_by(models.ContentPost.created_at.desc()).offset(offset).limit(limit).all()
    return {"total": total, "posts": posts}


@router.get("/posts/{post_id}")
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    post = db.query(models.ContentPost).filter_by(id=post_id, owner_id=current_user.id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    return post


@router.patch("/posts/{post_id}")
def update_post(
    post_id: int,
    data: ContentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    post = db.query(models.ContentPost).filter_by(id=post_id, owner_id=current_user.id).first()
    if not post:
        raise HTTPException(404, "Post not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(post, field, value)

    if data.status == "published" and not post.published_at:
        post.published_at = datetime.utcnow()

    post.updated_at = datetime.utcnow()
    db.commit()
    return {"updated": True, "post_id": post_id}


@router.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    post = db.query(models.ContentPost).filter_by(id=post_id, owner_id=current_user.id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    db.delete(post)
    db.commit()
    return {"deleted": True}


class BriefRequest(BaseModel):
    topic: str
    keyword: str
    competitors: Optional[List[str]] = []


class RepurposeRequest(BaseModel):
    source_content: str
    source_type: str = "blog"
    target_platforms: List[str] = ["instagram", "twitter", "linkedin"]


@router.post("/brief/generate")
async def generate_brief(
    data: BriefRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Generate a detailed content brief before writing."""
    agent = ContentAgent(db, current_user.id)
    return await agent.generate_content_brief(data.topic, data.keyword, data.competitors)


@router.post("/repurpose")
async def repurpose_content(
    data: RepurposeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Repurpose content into multiple platform-native formats via Social agent."""
    from agents.social_agent import SocialAgent
    agent = SocialAgent(db, current_user.id)
    return await agent.repurpose_content(
        data.source_content, data.source_type, data.target_platforms
    )
