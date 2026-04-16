"""CRM + WhatsApp MCP — leads, follow-ups, pipeline."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.database import get_db
from database import models
from core.dependencies import get_current_user
from agents.crm_agent import CRMAgent
from datetime import datetime
from typing import Optional, List

router = APIRouter(prefix="/crm", tags=["CRM + WhatsApp MCP"])


class LeadCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    company: Optional[str] = None
    source: str = "manual"
    deal_value: Optional[float] = None
    notes: Optional[str] = None
    tags: List[str] = []


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    deal_value: Optional[float] = None
    notes: Optional[str] = None
    next_follow_up: Optional[datetime] = None


class FollowUpRequest(BaseModel):
    lead_name: str
    company: str
    stage: str
    channel: str = "whatsapp"
    sequence_number: int = 1
    context: Optional[str] = None
    context: Optional[str] = None


class SendFollowUpRequest(BaseModel):
    channel: str
    message: str
    to: str


class PipelineRequest(BaseModel):
    interaction_history: List[str] = []


class BulkLeadImport(BaseModel):
    leads: List[LeadCreate]


@router.post("/leads", status_code=201)
def create_lead(
    data: LeadCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    lead = models.Lead(
        name=data.name,
        email=data.email,
        phone=data.phone,
        whatsapp=data.whatsapp,
        company=data.company,
        source=data.source,
        deal_value=data.deal_value,
        notes=data.notes,
        tags=data.tags,
        owner_id=current_user.id,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/leads")
def list_leads(
    status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Lead).filter_by(owner_id=current_user.id)
    if status:
        query = query.filter_by(status=status)
    if source:
        query = query.filter_by(source=source)
    if search:
        query = query.filter(
            models.Lead.name.ilike(f"%{search}%") |
            models.Lead.company.ilike(f"%{search}%") |
            models.Lead.email.ilike(f"%{search}%")
        )
    total = query.count()
    leads = query.order_by(models.Lead.created_at.desc()).offset(offset).limit(limit).all()
    return {"total": total, "leads": leads}


@router.get("/leads/{lead_id}")
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    lead = db.query(models.Lead).filter_by(id=lead_id, owner_id=current_user.id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    return lead


@router.patch("/leads/{lead_id}")
def update_lead(
    lead_id: int,
    data: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    lead = db.query(models.Lead).filter_by(id=lead_id, owner_id=current_user.id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(lead, field, value)
    lead.updated_at = datetime.utcnow()
    db.commit()
    return {"updated": True}


@router.delete("/leads/{lead_id}")
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    lead = db.query(models.Lead).filter_by(id=lead_id, owner_id=current_user.id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    db.delete(lead)
    db.commit()
    return {"deleted": True}


@router.post("/leads/{lead_id}/score")
async def score_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    lead = db.query(models.Lead).filter_by(id=lead_id, owner_id=current_user.id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")

    agent = CRMAgent(db, current_user.id)
    lead_data = {
        "id": lead.id,
        "name": lead.name,
        "company": lead.company,
        "source": lead.source,
        "deal_value": lead.deal_value,
        "status": lead.status.value,
        "notes": lead.notes,
    }
    result = await agent.score_lead(lead_data)

    lead.ai_score = result.get("score")
    db.commit()

    return result


@router.post("/leads/{lead_id}/followup/generate")
async def generate_followup(
    lead_id: int,
    data: FollowUpRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    agent = CRMAgent(db, current_user.id)
    return await agent.generate_followup_message(
        data.lead_name, data.company, data.stage, data.channel,
        data.context or "", data.sequence_number
    )


@router.post("/leads/{lead_id}/followup/send")
async def send_followup(
    lead_id: int,
    data: SendFollowUpRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    lead = db.query(models.Lead).filter_by(id=lead_id, owner_id=current_user.id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")

    agent = CRMAgent(db, current_user.id)
    result = await agent.send_followup(lead_id, data.channel, data.message, data.to, lead.name)

    # Log message
    msg = models.WhatsAppMessage(
        lead_id=lead_id,
        direction="outbound",
        message=data.message,
        is_ai_generated=True,
        status="sent" if result.get("success") else "failed",
    )
    db.add(msg)

    lead.last_contacted_at = datetime.utcnow()
    db.commit()

    return result


@router.post("/leads/{lead_id}/stage/suggest")
async def suggest_stage(
    lead_id: int,
    data: PipelineRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    lead = db.query(models.Lead).filter_by(id=lead_id, owner_id=current_user.id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    agent = CRMAgent(db, current_user.id)
    return await agent.suggest_pipeline_stage(
        {"name": lead.name, "company": lead.company, "status": lead.status.value},
        data.interaction_history,
    )


@router.get("/pipeline/report")
async def pipeline_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    leads = db.query(models.Lead).filter_by(owner_id=current_user.id).all()
    leads_data = [
        {"name": l.name, "status": l.status.value, "deal_value": l.deal_value or 0}
        for l in leads
    ]
    agent = CRMAgent(db, current_user.id)
    return await agent.generate_pipeline_report(leads_data)


@router.get("/messages/{lead_id}")
def get_lead_messages(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    lead = db.query(models.Lead).filter_by(id=lead_id, owner_id=current_user.id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    messages = (
        db.query(models.WhatsAppMessage)
        .filter_by(lead_id=lead_id)
        .order_by(models.WhatsAppMessage.sent_at.desc())
        .limit(50)
        .all()
    )
    return messages


@router.get("/sequence/due")
async def auto_sequence_check(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return all leads that are due for a follow-up today, with sequence context."""
    agent = CRMAgent(db, current_user.id)
    return await agent.auto_sequence_check(current_user.id)


@router.post("/leads/import")
def bulk_import(
    data: BulkLeadImport,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    created = 0
    for lead_data in data.leads:
        lead = models.Lead(
            name=lead_data.name,
            email=lead_data.email,
            phone=lead_data.phone,
            whatsapp=lead_data.whatsapp,
            company=lead_data.company,
            source=lead_data.source,
            deal_value=lead_data.deal_value,
            notes=lead_data.notes,
            tags=lead_data.tags,
            owner_id=current_user.id,
        )
        db.add(lead)
        created += 1
    db.commit()
    return {"imported": created}
