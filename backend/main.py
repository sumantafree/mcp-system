"""
╔══════════════════════════════════════════════════════════════╗
║          MCP SYSTEM — BACKEND ENTRY POINT                    ║
║  Modular Capability Programs — FastAPI Application           ║
╚══════════════════════════════════════════════════════════════╝
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from database.database import create_all_tables
from middleware.logging import RequestLoggingMiddleware

# Routers
from routers import auth, tasks, seo, content, social, youtube, crm, website, analytics, assistant

# ── Logging ──────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("mcp")


# ── Lifespan ─────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting MCP System...")
    create_all_tables()
    logger.info("Database tables ready.")
    yield
    logger.info("MCP System shutdown.")


# ── App ───────────────────────────────────
app = FastAPI(
    title="MCP System API",
    description="""
## Modular Capability Programs — AI-Powered Productivity System

### Modules:
| # | Module | Description |
|---|--------|-------------|
| 1 | Task Manager | NLP task creation, priority AI, notifications |
| 2 | SEO | Keyword clustering, meta generation, redirect automation |
| 3 | Content | Blog generation, news rewriting, multi-language |
| 4 | Social Media | Auto scheduling, hashtags, content calendar |
| 5 | YouTube | Scripts, title optimization, Shorts |
| 6 | CRM + WhatsApp | Lead scoring, automated follow-ups |
| 7 | Website | Broken link detection, auto page generation |
| 8 | Analytics | Dashboard, weekly reports, AI insights |
| 9 | ARIA Assistant | Natural language controller for all MCPs |
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── Middleware ────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://mcp-system-cyan.vercel.app",
        "http://localhost:3000",  # optional for testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)


# ── Routers ───────────────────────────────
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(seo.router)
app.include_router(content.router)
app.include_router(social.router)
app.include_router(youtube.router)
app.include_router(crm.router)
app.include_router(website.router)
app.include_router(analytics.router)
app.include_router(assistant.router)


# ── Health & Root ─────────────────────────
@app.get("/", tags=["System"])
def root():
    return {
        "system": "MCP System",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "modules": [
            "tasks", "seo", "content", "social",
            "youtube", "crm", "website", "analytics", "assistant"
        ],
    }


@app.get("/health", tags=["System"])
def health():
    return {"status": "healthy", "env": settings.APP_ENV}


# ── Cross-Module Pipeline Endpoints ──────────
from fastapi import Depends
from database.database import get_db
from core.dependencies import get_current_user
from database import models as _models
from pydantic import BaseModel as _BaseModel
from typing import List as _List
from agents import (
    run_seo_to_content_pipeline,
    run_content_to_social_pipeline,
    run_crm_auto_followup_pipeline,
)


class SEOToContentRequest(_BaseModel):
    topic: str
    keywords: _List[str]


class ContentToSocialRequest(_BaseModel):
    blog_title: str
    platforms: _List[str] = ["instagram", "twitter", "linkedin"]


@app.post("/pipelines/seo-to-content", tags=["Pipelines"])
async def pipeline_seo_to_content(
    data: SEOToContentRequest,
    db=Depends(get_db),
    current_user: _models.User = Depends(get_current_user),
):
    """Pipeline: Cluster keywords → pick best → generate full blog."""
    return await run_seo_to_content_pipeline(db, current_user.id, data.topic, data.keywords)


@app.post("/pipelines/content-to-social", tags=["Pipelines"])
async def pipeline_content_to_social(
    data: ContentToSocialRequest,
    db=Depends(get_db),
    current_user: _models.User = Depends(get_current_user),
):
    """Pipeline: Blog title → generate platform-native posts for all platforms."""
    return await run_content_to_social_pipeline(db, current_user.id, data.blog_title, data.platforms)


@app.post("/pipelines/crm-auto-followup", tags=["Pipelines"])
async def pipeline_crm_followup(
    db=Depends(get_db),
    current_user: _models.User = Depends(get_current_user),
):
    """Pipeline: Check all due leads → generate follow-up messages (review before sending)."""
    return await run_crm_auto_followup_pipeline(db, current_user.id)


# ── Global Error Handler ──────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
