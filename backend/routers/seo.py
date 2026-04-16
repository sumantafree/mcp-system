"""SEO MCP — keyword clustering, meta generation, redirects."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.database import get_db
from database import models
from core.dependencies import get_current_user
from agents.seo_agent import SEOAgent
from typing import List, Optional

router = APIRouter(prefix="/seo", tags=["SEO MCP"])


class KeywordClusterRequest(BaseModel):
    keywords: List[str]
    language: str = "en"


class MetaGenerateRequest(BaseModel):
    page_title: str
    content_snippet: str
    keyword: str
    language: str = "en"


class InternalLinkRequest(BaseModel):
    current_page_title: str
    existing_pages: List[dict]


class RedirectRequest(BaseModel):
    broken_url: str
    available_pages: List[str]


class ContentAuditRequest(BaseModel):
    content: str
    keyword: str


class SaveKeywordRequest(BaseModel):
    keyword: str
    cluster_name: Optional[str] = None
    language: str = "en"
    search_volume: Optional[int] = None
    difficulty: Optional[float] = None


@router.post("/keywords/cluster")
async def cluster_keywords(
    data: KeywordClusterRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not data.keywords:
        raise HTTPException(400, "Keywords list cannot be empty")
    agent = SEOAgent(db, current_user.id)
    return await agent.cluster_keywords(data.keywords, data.language)


@router.post("/meta/generate")
async def generate_meta(
    data: MetaGenerateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = SEOAgent(db, current_user.id)
    result = await agent.generate_meta(
        data.page_title, data.content_snippet, data.keyword, data.language
    )
    # Save to DB
    meta = models.SEOMeta(
        page_url=data.page_title,
        meta_title=result.get("meta_title"),
        meta_description=result.get("meta_description"),
        og_title=result.get("og_title"),
        og_description=result.get("og_description"),
        focus_keyword=data.keyword,
        language=data.language,
        owner_id=current_user.id,
    )
    db.add(meta)
    db.commit()
    return {**result, "saved_id": meta.id}


@router.get("/meta/list")
def list_meta(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    records = db.query(models.SEOMeta).filter_by(owner_id=current_user.id).order_by(
        models.SEOMeta.created_at.desc()
    ).limit(50).all()
    return records


@router.post("/links/internal")
async def suggest_internal_links(
    data: InternalLinkRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = SEOAgent(db, current_user.id)
    return await agent.suggest_internal_links(data.current_page_title, data.existing_pages)


@router.post("/redirect/suggest")
async def suggest_redirect(
    data: RedirectRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = SEOAgent(db, current_user.id)
    result = await agent.generate_redirect_suggestion(data.broken_url, data.available_pages)

    # Update broken link record if exists
    bl = db.query(models.BrokenLink).filter_by(
        broken_url=data.broken_url, owner_id=current_user.id
    ).first()
    if bl and result.get("redirect_to"):
        bl.redirect_to = result["redirect_to"]
        db.commit()

    return result


@router.get("/broken-links")
def list_broken_links(
    is_fixed: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.BrokenLink).filter_by(owner_id=current_user.id)
    if is_fixed is not None:
        query = query.filter_by(is_fixed=is_fixed)
    return query.order_by(models.BrokenLink.detected_at.desc()).limit(100).all()


@router.patch("/broken-links/{link_id}/fix")
def mark_link_fixed(
    link_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    from datetime import datetime
    link = db.query(models.BrokenLink).filter_by(id=link_id, owner_id=current_user.id).first()
    if not link:
        raise HTTPException(404, "Broken link not found")
    link.is_fixed = True
    link.fixed_at = datetime.utcnow()
    db.commit()
    return {"fixed": True}


@router.post("/audit")
async def audit_content(
    data: ContentAuditRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = SEOAgent(db, current_user.id)
    return await agent.audit_content_seo(data.content, data.keyword)


@router.post("/keywords/save")
def save_keyword(
    data: SaveKeywordRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    kw = models.SEOKeyword(
        keyword=data.keyword,
        cluster_name=data.cluster_name,
        language=data.language,
        search_volume=data.search_volume,
        difficulty=data.difficulty,
        owner_id=current_user.id,
    )
    db.add(kw)
    db.commit()
    db.refresh(kw)
    return kw


@router.get("/keywords/list")
def list_keywords(
    language: Optional[str] = Query(None),
    cluster: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.SEOKeyword).filter_by(owner_id=current_user.id)
    if language:
        query = query.filter_by(language=language)
    if cluster:
        query = query.filter_by(cluster_name=cluster)
    return query.order_by(models.SEOKeyword.created_at.desc()).limit(200).all()


class TopicClusterRequest(BaseModel):
    pillar_topic: str
    language: str = "en"


@router.post("/topic-cluster")
async def generate_topic_cluster(
    data: TopicClusterRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Generate a full hub-and-spoke topic cluster (pillar + spoke pages)."""
    agent = SEOAgent(db, current_user.id)
    return await agent.generate_topic_cluster(data.pillar_topic, data.language)
