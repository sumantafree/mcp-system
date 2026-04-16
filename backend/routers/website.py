"""Website MCP — broken links, auto pages, performance."""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.database import get_db
from database import models
from core.dependencies import get_current_user
from agents.website_agent import WebsiteAgent
from typing import Optional

router = APIRouter(prefix="/website", tags=["Website MCP"])


class ScanRequest(BaseModel):
    website_url: str
    max_pages: int = 50


class PageGenerateRequest(BaseModel):
    page_type: str = "landing"
    keyword: str
    business_info: dict = {}
    language: str = "en"


class PerformanceRequest(BaseModel):
    url: str


class OptimizationRequest(BaseModel):
    scan_result: dict


@router.post("/scan")
async def scan_website(
    data: ScanRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Crawl website and detect broken links."""
    agent = WebsiteAgent(db, current_user.id)

    # Create scan record
    scan = models.WebsiteScan(
        website_url=data.website_url,
        status="running",
        owner_id=current_user.id,
    )
    db.add(scan)
    db.commit()

    try:
        result = await agent.scan_broken_links(data.website_url, data.max_pages)
        scan.status = "completed"
        scan.broken_links_count = result["broken_count"]
        scan.total_pages = result["pages_crawled"]
        scan.completed_at = __import__("datetime").datetime.utcnow()
        db.commit()
        return {**result, "scan_id": scan.id}
    except Exception as e:
        scan.status = "failed"
        db.commit()
        raise HTTPException(500, f"Scan failed: {str(e)}")


@router.get("/scans")
def list_scans(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    scans = (
        db.query(models.WebsiteScan)
        .filter_by(owner_id=current_user.id)
        .order_by(models.WebsiteScan.started_at.desc())
        .limit(20)
        .all()
    )
    return scans


@router.post("/pages/generate", status_code=201)
async def generate_page(
    data: PageGenerateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """AI-generate a complete web page."""
    agent = WebsiteAgent(db, current_user.id)
    result = await agent.generate_page(
        data.page_type, data.keyword, data.business_info, data.language
    )

    page = models.AutoPage(
        page_title=result.get("page_title", data.keyword),
        page_slug=result.get("slug"),
        page_content=result.get("content"),
        page_type=data.page_type,
        target_keyword=data.keyword,
        status="draft",
        owner_id=current_user.id,
    )
    db.add(page)
    db.commit()
    db.refresh(page)

    return {**result, "page_id": page.id}


@router.get("/pages")
def list_pages(
    page_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.AutoPage).filter_by(owner_id=current_user.id)
    if page_type:
        query = query.filter_by(page_type=page_type)
    return query.order_by(models.AutoPage.created_at.desc()).limit(50).all()


@router.get("/pages/{page_id}")
def get_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    page = db.query(models.AutoPage).filter_by(id=page_id, owner_id=current_user.id).first()
    if not page:
        raise HTTPException(404, "Page not found")
    return page


@router.post("/performance")
async def analyze_performance(
    data: PerformanceRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Analyze page performance."""
    agent = WebsiteAgent(db, current_user.id)
    result = await agent.analyze_performance(data.url)
    return result


@router.post("/optimize")
async def get_optimization_plan(
    data: OptimizationRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get AI optimization recommendations."""
    agent = WebsiteAgent(db, current_user.id)
    plan = await agent.generate_optimization_plan(data.scan_result)
    return {"optimization_plan": plan}


@router.get("/broken-links")
def list_broken_links(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    links = (
        db.query(models.BrokenLink)
        .filter_by(owner_id=current_user.id, is_fixed=False)
        .order_by(models.BrokenLink.detected_at.desc())
        .limit(100)
        .all()
    )
    return links
