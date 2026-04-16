"""Personal AI Assistant MCP — ARIA controller v2

New endpoints:
- POST /assistant/command     — full ReAct execution
- POST /assistant/chat        — multi-turn chat with history
- GET  /assistant/stream      — streaming chat via SSE
- GET  /assistant/briefing    — daily briefing with CoT
- GET  /assistant/suggestions — proactive AI suggestions
- POST /assistant/route       — intent preview (no execution)
- WS   /assistant/ws/{id}     — real-time WebSocket chat
"""
import json
import asyncio
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.database import get_db
from database import models
from core.dependencies import get_current_user
from agents.personal_agent import PersonalAgent
from typing import Optional, List

router = APIRouter(prefix="/assistant", tags=["Personal AI Assistant MCP"])


# ── Schemas ──────────────────────────────

class CommandRequest(BaseModel):
    message: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[dict]] = []


# ── Endpoints ────────────────────────────

@router.post("/command")
async def process_command(
    data: CommandRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Full ReAct loop — Plan → Act → Reflect. Handles single and multi-step requests."""
    agent = PersonalAgent(db, current_user.id)
    return await agent.process_command(data.message)


@router.post("/chat")
async def chat(
    data: ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Multi-turn chat with persistent conversation history."""
    agent = PersonalAgent(db, current_user.id)
    response = await agent.chat(data.message, data.conversation_history)
    return {"response": response, "agent": "ARIA"}


@router.get("/stream")
async def stream_chat(
    message: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Server-Sent Events streaming chat response."""
    agent = PersonalAgent(db, current_user.id)

    async def event_generator():
        try:
            async for chunk in agent.chat_stream(message):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/briefing")
async def daily_briefing(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Personalized daily briefing with CoT reasoning."""
    agent = PersonalAgent(db, current_user.id)
    return await agent.generate_daily_briefing(current_user.id)


@router.get("/suggestions")
async def proactive_suggestions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """AI-generated proactive action suggestions based on cross-module activity."""
    agent = PersonalAgent(db, current_user.id)
    suggestions = await agent.get_proactive_suggestions()
    return {"suggestions": suggestions}


@router.post("/route")
async def route_intent(
    data: CommandRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Preview intent routing without executing."""
    agent = PersonalAgent(db, current_user.id)
    return await agent.route_intent(data.message)


@router.delete("/history")
def clear_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Clear conversation history for the current user."""
    agent = PersonalAgent(db, current_user.id)
    agent.clear_history()
    return {"cleared": True}


@router.get("/history")
def get_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return current conversation history."""
    agent = PersonalAgent(db, current_user.id)
    return {"history": agent.get_conversation_history()}


# ── WebSocket ─────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.connections: dict[int, WebSocket] = {}

    async def connect(self, user_id: int, ws: WebSocket):
        await ws.accept()
        self.connections[user_id] = ws

    def disconnect(self, user_id: int):
        self.connections.pop(user_id, None)

    async def send(self, user_id: int, data: dict):
        ws = self.connections.get(user_id)
        if ws:
            await ws.send_text(json.dumps(data))


manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_aria(
    websocket: WebSocket,
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Real-time ARIA WebSocket.
    Supports:
    - {"type": "command", "message": "..."} → full ReAct execution
    - {"type": "chat", "message": "..."}    → conversational reply
    - {"type": "stream", "message": "..."}  → streamed token-by-token reply
    - {"type": "ping"}                       → keep-alive
    """
    await manager.connect(user_id, websocket)
    agent = PersonalAgent(db, user_id)

    try:
        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)
            msg_type = payload.get("type", "chat")
            message  = payload.get("message", "")

            if msg_type == "ping":
                await manager.send(user_id, {"type": "pong"})
                continue

            # Acknowledge receipt immediately
            await manager.send(user_id, {"type": "thinking", "message": "ARIA is thinking..."})

            if msg_type == "command":
                result = await agent.process_command(message)
                await manager.send(user_id, {"type": "command_result", "data": result})

            elif msg_type == "stream":
                await manager.send(user_id, {"type": "stream_start"})
                async for chunk in agent.chat_stream(message):
                    await manager.send(user_id, {"type": "chunk", "text": chunk})
                    await asyncio.sleep(0)  # yield to event loop
                await manager.send(user_id, {"type": "stream_end"})

            else:  # "chat"
                response = await agent.chat(message)
                await manager.send(user_id, {"type": "chat_response", "response": response})

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "error": str(e)}))
        manager.disconnect(user_id)
