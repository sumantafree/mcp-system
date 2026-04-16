"""Analytics MCP — dashboard, weekly reports, insights."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database.database import get_db
from database import models
from core.dependencies import get_current_user
from agents.analytics_agent import AnalyticsAgent

router = APIRouter(prefix="/analytics", tags=["Analytics MCP"])


@router.get("/dashboard")
def get_dashboard(
    days: int = Query(7, le=90),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Real-time dashboard metrics."""
    agent = AnalyticsAgent(db, current_user.id)
    return agent.get_dashboard_metrics(current_user.id, days)


@router.post("/reports/weekly")
async def generate_weekly_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Generate AI weekly report."""
    agent = AnalyticsAgent(db, current_user.id)
    return await agent.generate_weekly_report(current_user.id)


@router.get("/reports")
def list_reports(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    reports = (
        db.query(models.WeeklyReport)
        .filter_by(owner_id=current_user.id)
        .order_by(models.WeeklyReport.generated_at.desc())
        .limit(10)
        .all()
    )
    return reports


@router.get("/activity")
def get_activity(
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = AnalyticsAgent(db, current_user.id)
    return agent.get_activity_timeline(current_user.id, limit)


@router.get("/notifications")
def get_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Notification).filter_by(user_id=current_user.id)
    if unread_only:
        query = query.filter_by(is_read=False)
    return query.order_by(models.Notification.created_at.desc()).limit(limit).all()


@router.patch("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    notif = db.query(models.Notification).filter_by(
        id=notification_id, user_id=current_user.id
    ).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"read": True}


@router.get("/health")
def module_health_scores(
    days: int = Query(7, le=90),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return health score (0-100) per MCP module."""
    agent = AnalyticsAgent(db, current_user.id)
    metrics = agent.get_dashboard_metrics(current_user.id, days)
    return agent.compute_module_health_scores(metrics)


@router.get("/anomalies")
def detect_anomalies(
    days: int = Query(7, le=90),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Detect unusual drops or spikes across all modules."""
    agent = AnalyticsAgent(db, current_user.id)
    metrics = agent.get_dashboard_metrics(current_user.id, days)
    return agent.detect_anomalies(metrics)


@router.patch("/notifications/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db.query(models.Notification).filter_by(
        user_id=current_user.id, is_read=False
    ).update({"is_read": True})
    db.commit()
    return {"marked_read": True}


@router.post("/insights/{module}")
async def module_insights(
    module: str,
    data: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = AnalyticsAgent(db, current_user.id)
    insights = await agent.get_module_insights(module, data)
    return {"module": module, "insights": insights}
