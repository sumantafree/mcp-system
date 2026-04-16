"""Task Manager MCP — full CRUD + AI endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.database import get_db
from database import models
from core.dependencies import get_current_user
from agents.task_agent import TaskAgent
from integrations.email_service import send_task_reminder
from integrations.whatsapp_service import send_task_alert_whatsapp
from datetime import datetime
from typing import Optional, List

router = APIRouter(prefix="/tasks", tags=["Task Manager MCP"])


# ── Schemas ──────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    status: Optional[str] = "todo"
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = []
    estimated_hours: Optional[float] = None
    project_id: Optional[int] = None
    assigned_to_id: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None


class TaskFromTextRequest(BaseModel):
    text: str


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#3B82F6"
    deadline: Optional[datetime] = None


# ── Task CRUD ────────────────────────────

@router.get("/")
def list_tasks(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    project_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Task).filter_by(owner_id=current_user.id)

    if status:
        query = query.filter(models.Task.status == status)
    if priority:
        query = query.filter(models.Task.priority == priority)
    if project_id:
        query = query.filter_by(project_id=project_id)
    if search:
        query = query.filter(models.Task.title.ilike(f"%{search}%"))

    total = query.count()
    tasks = query.order_by(models.Task.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "priority": t.priority.value,
                "status": t.status.value,
                "due_date": t.due_date,
                "tags": t.tags,
                "estimated_hours": t.estimated_hours,
                "ai_summary": t.ai_summary,
                "project_id": t.project_id,
                "created_at": t.created_at,
            }
            for t in tasks
        ],
    }


@router.post("/", status_code=201)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = models.Task(
        title=data.title,
        description=data.description,
        priority=data.priority,
        status=data.status,
        due_date=data.due_date,
        tags=data.tags,
        estimated_hours=data.estimated_hours,
        project_id=data.project_id,
        assigned_to_id=data.assigned_to_id,
        owner_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"id": task.id, "title": task.title, "status": task.status.value}


@router.get("/{task_id}")
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = db.query(models.Task).filter_by(id=task_id, owner_id=current_user.id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.patch("/{task_id}")
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = db.query(models.Task).filter_by(id=task_id, owner_id=current_user.id).first()
    if not task:
        raise HTTPException(404, "Task not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(task, field, value)

    if data.status == "done" and not task.completed_at:
        task.completed_at = datetime.utcnow()

    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return {"id": task.id, "status": task.status.value, "updated": True}


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = db.query(models.Task).filter_by(id=task_id, owner_id=current_user.id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    db.delete(task)
    db.commit()
    return {"deleted": True}


# ── AI Endpoints ─────────────────────────

@router.post("/ai/from-text")
async def create_from_text(
    data: TaskFromTextRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Create task from natural language description."""
    agent = TaskAgent(db, current_user.id)
    parsed = await agent.create_task_from_text(data.text)

    task = models.Task(
        title=parsed.get("title", data.text[:100]),
        description=parsed.get("description"),
        priority=parsed.get("priority", "medium"),
        tags=parsed.get("tags", []),
        estimated_hours=parsed.get("estimated_hours"),
        ai_summary=parsed.get("ai_summary"),
        owner_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return {"task_id": task.id, "parsed": parsed, "created": True}


@router.get("/ai/suggestions")
async def get_ai_suggestions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get AI-powered task suggestions."""
    agent = TaskAgent(db, current_user.id)
    return await agent.get_ai_suggestions(current_user.id)


@router.get("/ai/briefing")
async def get_daily_briefing(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get AI daily task briefing."""
    agent = TaskAgent(db, current_user.id)
    tasks = (
        db.query(models.Task)
        .filter_by(owner_id=current_user.id, status="todo")
        .order_by(models.Task.due_date)
        .limit(10)
        .all()
    )
    task_dicts = [
        {"title": t.title, "priority": t.priority.value, "due_date": str(t.due_date)}
        for t in tasks
    ]
    briefing = await agent.generate_daily_briefing(task_dicts)
    return {"briefing": briefing}


@router.post("/{task_id}/notify")
async def send_task_notification(
    task_id: int,
    channel: str = Query("email", regex="^(email|whatsapp)$"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Send task reminder via email or WhatsApp."""
    task = db.query(models.Task).filter_by(id=task_id, owner_id=current_user.id).first()
    if not task:
        raise HTTPException(404, "Task not found")

    due_str = task.due_date.strftime("%Y-%m-%d %H:%M") if task.due_date else "No deadline"

    if channel == "email" and current_user.email:
        result = await send_task_reminder(current_user.email, task.title, due_str)
        return {"channel": "email", "sent": result}
    elif channel == "whatsapp" and current_user.whatsapp_number:
        result = await send_task_alert_whatsapp(current_user.whatsapp_number, task.title, due_str)
        return {"channel": "whatsapp", "result": result}
    else:
        raise HTTPException(400, f"No {channel} address configured for user")


# ── Projects ─────────────────────────────

@router.get("/projects/list")
def list_projects(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    projects = db.query(models.Project).filter_by(owner_id=current_user.id, is_active=True).all()
    return projects


@router.post("/projects", status_code=201)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    project = models.Project(
        name=data.name,
        description=data.description,
        color=data.color,
        deadline=data.deadline,
        owner_id=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project
