"""
Base MCP Agent — v2

Improvements over v1:
- Conversation history (full multi-turn context, not just last command)
- Rich context window (user profile + recent activity injected automatically)
- Chain-of-thought via ai.think_then_answer()
- Self-reflection via ai.reflect()
- Cross-module memory sharing
- Structured error handling per agent action
- Agent-to-agent messaging (publish/subscribe via shared DB)
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from database import models
from integrations.ai_client import AIClient
from agents.prompt_templates import SYSTEM_PROMPTS, CONTEXT_INJECTION_TEMPLATE

logger = logging.getLogger("mcp.agent")


class BaseMCPAgent:
    MODULE_NAME: str = "base"
    MAX_HISTORY_TURNS: int = 10      # conversation turns to keep in memory
    CONTEXT_WINDOW_TOKENS: int = 3000  # max chars of context to inject

    def __init__(self, db: Session, user_id: int, provider: Optional[str] = None):
        self.db = db
        self.user_id = user_id
        self.ai = AIClient(provider)
        self._system_prompt = SYSTEM_PROMPTS.get(self.MODULE_NAME, "")

    # ── System prompt shortcut ──────────────────────────────────────────

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

    # ── Conversation History ────────────────────────────────────────────

    def add_to_history(self, role: str, content: str):
        """Persist a conversation turn (user or assistant message)."""
        key = f"history_{self.MODULE_NAME}"
        existing_raw = self._get_raw_memory(f"{key}")
        turns = json.loads(existing_raw) if existing_raw else []
        turns.append({"role": role, "content": content, "ts": datetime.utcnow().isoformat()})
        # Keep only last N turns
        turns = turns[-self.MAX_HISTORY_TURNS * 2:]
        self._set_raw_memory(key, json.dumps(turns), ttl_minutes=480)

    def get_conversation_history(self) -> list[dict]:
        """Return recent conversation history as [{role, content}]."""
        key = f"history_{self.MODULE_NAME}"
        raw = self._get_raw_memory(key)
        if not raw:
            return []
        turns = json.loads(raw)
        return [{"role": t["role"], "content": t["content"]} for t in turns]

    def clear_history(self):
        self._set_raw_memory(f"history_{self.MODULE_NAME}", "[]")

    # ── Context Building ────────────────────────────────────────────────

    def build_context(self) -> str:
        """
        Assemble a rich context string injected before prompts:
        - User profile (name, role, timezone)
        - Recent module activity (last 5 events)
        - Cross-module memory (important keys from other modules)
        """
        user = self.db.query(models.User).filter_by(id=self.user_id).first()
        user_profile = f"{user.full_name} ({user.role.value})" if user else "Unknown user"

        recent_events = (
            self.db.query(models.AnalyticsEvent)
            .filter_by(user_id=self.user_id, module=self.MODULE_NAME)
            .order_by(models.AnalyticsEvent.timestamp.desc())
            .limit(5)
            .all()
        )
        activity_summary = ", ".join([e.event_type for e in recent_events]) or "No recent activity"

        # Pull cross-module shared memories
        shared_memories = (
            self.db.query(models.AIMemory)
            .filter_by(user_id=self.user_id, module="shared")
            .filter(models.AIMemory.expires_at > datetime.utcnow())
            .limit(5)
            .all()
        )
        shared_str = "; ".join([f"{m.memory_key}: {m.memory_value}" for m in shared_memories]) or "None"

        return (
            f"User: {user_profile} | "
            f"Recent {self.MODULE_NAME} activity: {activity_summary} | "
            f"Shared context: {shared_str}"
        )[:self.CONTEXT_WINDOW_TOKENS]

    def inject_context(self, prompt: str) -> str:
        """Prepend context to a prompt for richer AI responses."""
        ctx = self.build_context()
        if not ctx:
            return prompt
        return f"[Context: {ctx}]\n\n{prompt}"

    # ── Memory (key-value, scoped per module) ───────────────────────────

    def save_memory(self, key: str, value: str, ttl_minutes: int = 1440):
        self._set_raw_memory(key, value, ttl_minutes)

    def recall_memory(self, key: str) -> Optional[str]:
        return self._get_raw_memory(key)

    def save_shared_memory(self, key: str, value: str, ttl_minutes: int = 1440):
        """Save memory accessible to all modules (cross-agent context)."""
        self._set_raw_memory(key, value, ttl_minutes, module_override="shared")

    def recall_shared_memory(self, key: str) -> Optional[str]:
        return self._get_raw_memory(key, module_override="shared")

    def _set_raw_memory(
        self, key: str, value: str, ttl_minutes: int = 1440, module_override: Optional[str] = None
    ):
        module = module_override or self.MODULE_NAME
        existing = (
            self.db.query(models.AIMemory)
            .filter_by(user_id=self.user_id, module=module, memory_key=key)
            .first()
        )
        expires = datetime.utcnow() + timedelta(minutes=ttl_minutes)
        if existing:
            existing.memory_value = value
            existing.updated_at = datetime.utcnow()
            existing.expires_at = expires
        else:
            self.db.add(models.AIMemory(
                user_id=self.user_id,
                module=module,
                memory_key=key,
                memory_value=value,
                expires_at=expires,
            ))
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Memory save failed: {e}")

    def _get_raw_memory(self, key: str, module_override: Optional[str] = None) -> Optional[str]:
        module = module_override or self.MODULE_NAME
        mem = (
            self.db.query(models.AIMemory)
            .filter_by(user_id=self.user_id, module=module, memory_key=key)
            .filter(models.AIMemory.expires_at > datetime.utcnow())
            .first()
        )
        return mem.memory_value if mem else None

    # ── Agent-to-Agent Messaging ────────────────────────────────────────

    def send_to_agent(self, target_module: str, message_key: str, data: str):
        """
        Publish a result to another agent's memory.
        Enables pipeline: SEO agent → publishes best keyword → Content agent picks it up.
        """
        key = f"from_{self.MODULE_NAME}_{message_key}"
        self._set_raw_memory(key, data, ttl_minutes=60, module_override=target_module)
        logger.info(f"[{self.MODULE_NAME}] → [{target_module}]: {message_key}")

    def receive_from_agent(self, source_module: str, message_key: str) -> Optional[str]:
        """Read a message sent by another agent."""
        key = f"from_{source_module}_{message_key}"
        return self._get_raw_memory(key)

    # ── Reasoning Helpers ───────────────────────────────────────────────

    async def think(self, question: str, context: Optional[str] = None) -> dict:
        """
        Chain-of-thought reasoning before acting.
        Use this for complex decisions, not simple generations.
        """
        return await self.ai.think_then_answer(question, self.system_prompt, context)

    async def reflect_on_output(self, output: str, task: str) -> dict:
        """Self-evaluate and optionally improve output."""
        return await self.ai.reflect(output, task)

    # ── Logging & Tracking ──────────────────────────────────────────────

    def log_activity(
        self,
        action: str,
        entity_type: str = None,
        entity_id: int = None,
        details: dict = None,
    ):
        log = models.ActivityLog(
            user_id=self.user_id,
            action=action,
            module=self.MODULE_NAME,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
        )
        self.db.add(log)
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Activity log failed: {e}")

    def track_event(self, event_type: str, metadata: dict = None):
        event = models.AnalyticsEvent(
            event_type=event_type,
            module=self.MODULE_NAME,
            user_id=self.user_id,
            meta_data=metadata or {},
        )
        self.db.add(event)
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Event tracking failed: {e}")

    def notify_user(self, title: str, body: str, action_url: str = None):
        """Create an in-app notification for the user."""
        notif = models.Notification(
            user_id=self.user_id,
            title=title,
            body=body,
            type=models.NotificationType.in_app,
            action_url=action_url,
        )
        self.db.add(notif)
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Notification failed: {e}")
