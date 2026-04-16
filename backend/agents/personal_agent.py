"""
MCP 9: ARIA — Personal AI Assistant (Main Controller) v2

Improvements over v1:
- Full ReAct loop via ReasoningEngine (Plan → Act → Reflect)
- Persistent multi-turn conversation history
- Context-aware responses (user profile + recent activity)
- Multi-step workflow detection and execution
- Streaming support for chat responses
- Proactive suggestions based on activity patterns
"""
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional

from sqlalchemy.orm import Session

from agents.base_agent import BaseMCPAgent
from agents.reasoning_engine import ReasoningEngine
from agents.analytics_agent import AnalyticsAgent
from agents.prompt_templates import SYSTEM_PROMPTS
from database import models

logger = logging.getLogger("mcp.aria")


class PersonalAgent(BaseMCPAgent):
    MODULE_NAME = "assistant"

    # ── Main command processor (ReAct) ─────────────────────────────────

    async def process_command(self, user_message: str) -> dict:
        """
        Process any natural language command using the full ReAct loop.
        Routes single or multi-step requests to the right MCP agents.
        """
        # Build rich context for planning
        context = self.build_context()

        # Add to conversation history
        self.add_to_history("user", user_message)

        # Run ReAct engine
        engine = ReasoningEngine(self.db, self.user_id)
        result = await engine.run(user_message, context)

        # Store final answer in history
        if result.get("final_answer"):
            self.add_to_history("assistant", result["final_answer"])

        # Update shared memory for cross-agent context
        self.save_shared_memory("last_command", user_message)
        self.save_shared_memory("last_module", result.get("routing", {}).get("module", "general"))

        self.track_event("command_processed", {
            "module": result.get("routing", {}).get("module"),
            "multi_step": result.get("is_multi_step", False),
            "steps": result.get("steps_executed", 1),
        })

        return result

    # ── Chat with full conversation history ────────────────────────────

    async def chat(self, message: str, conversation_history: Optional[list] = None) -> str:
        """
        Conversational chat with persistent history + context injection.
        Falls back to direct AI if no specific action needed.
        """
        self.add_to_history("user", message)

        # Use provided history or load from DB
        history = conversation_history or self.get_conversation_history()
        context = self.build_context()

        # Check if this needs ReAct routing or is pure conversation
        is_action = await self._is_action_request(message)

        if is_action:
            engine = ReasoningEngine(self.db, self.user_id)
            result = await engine.run(message, context)
            response = result.get("final_answer", "I processed your request.")
        else:
            # Pure conversation — use history for continuity
            system = SYSTEM_PROMPTS["assistant"]
            full_prompt = f"[Context: {context}]\n\nUser: {message}"
            response = await self.ai.generate(
                full_prompt,
                system,
                temperature=0.8,
                max_tokens=500,
                conversation=history[-6:] if history else None,  # last 3 turns
            )

        self.add_to_history("assistant", response)
        return response

    async def chat_stream(self, message: str) -> AsyncGenerator[str, None]:
        """Streaming chat response for real-time WebSocket."""
        context = self.build_context()
        history = self.get_conversation_history()
        self.add_to_history("user", message)

        full_prompt = f"[Context: {context}]\n\n{message}"
        full_response = ""
        async for chunk in self.ai.stream(full_prompt, SYSTEM_PROMPTS["assistant"]):
            full_response += chunk
            yield chunk

        self.add_to_history("assistant", full_response)

    # ── Intent preview (no execution) ─────────────────────────────────

    async def route_intent(self, user_message: str) -> dict:
        """Classify intent without executing — useful for UI preview."""
        engine = ReasoningEngine(self.db, self.user_id)
        return await engine._route_intent(user_message)

    # ── Daily Briefing ─────────────────────────────────────────────────

    async def generate_daily_briefing(self, user_id: int) -> dict:
        """Generate personalized daily briefing with CoT reasoning."""
        analytics = AnalyticsAgent(self.db, user_id)
        metrics = analytics.get_dashboard_metrics(user_id, days=1)

        from datetime import date
        today_start = datetime.combine(date.today(), datetime.min.time())
        tasks = (
            self.db.query(models.Task)
            .filter(
                models.Task.owner_id == user_id,
                models.Task.due_date >= today_start,
                models.Task.status != models.TaskStatus.done,
            )
            .order_by(models.Task.priority)
            .limit(5)
            .all()
        )
        task_list = [
            {"title": t.title, "priority": t.priority.value, "due_date": str(t.due_date)}
            for t in tasks
        ]

        # Use CoT for better briefing quality
        question = f"""What should this user focus on today?
Date: {datetime.utcnow().strftime('%A, %B %d, %Y')}
Today's tasks: {task_list}
Yesterday's metrics: tasks_completed={metrics['tasks']['completed']}, new_leads={metrics['crm']['new_leads']}"""

        cot_result = await self.ai.think_then_answer(question, SYSTEM_PROMPTS["assistant"])

        # Generate the actual briefing from the reasoning
        briefing_prompt = f"""Based on this analysis: {cot_result['reasoning'][:600]}

Write a concise, motivating daily briefing (under 200 words):
- Good morning opener
- Top 3 priorities for today
- One productivity tip
- Encouraging close"""

        briefing = await self.ai.generate(briefing_prompt, SYSTEM_PROMPTS["assistant"], temperature=0.8)

        return {
            "briefing": briefing,
            "reasoning": cot_result["reasoning"],
            "today_tasks": task_list,
            "metrics": metrics,
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ── Proactive suggestions ───────────────────────────────────────────

    async def get_proactive_suggestions(self) -> list[dict]:
        """
        Analyze user's cross-module activity and suggest actions
        they haven't taken but should.
        """
        metrics = AnalyticsAgent(self.db, self.user_id).get_dashboard_metrics(self.user_id, days=7)
        context = self.build_context()

        prompt = f"""Analyze this user's MCP system usage and suggest 3 high-value actions:

7-day metrics: {metrics}
Context: {context}

Identify gaps: tasks overdue? leads not followed up? no content published? no SEO work?

Return JSON:
{{
  "suggestions": [
    {{
      "title": "short action title",
      "description": "why this matters",
      "module": "which MCP module",
      "action_command": "what user should type to ARIA",
      "urgency": "high|medium|low",
      "estimated_impact": "what this will achieve"
    }}
  ]
}}"""
        response = await self.ai.generate(
            prompt, SYSTEM_PROMPTS["assistant"], temperature=0.6, json_mode=True
        )
        result = self.ai.parse_json_response(response)
        self.track_event("proactive_suggestions_generated")
        return result.get("suggestions", [])

    # ── Helpers ─────────────────────────────────────────────────────────

    async def _is_action_request(self, message: str) -> bool:
        """Quick check: is this a task/action or just conversation?"""
        action_keywords = [
            "create", "generate", "write", "make", "schedule", "analyze",
            "scan", "add", "show", "list", "get", "find", "send",
            "score", "audit", "optimize", "translate", "suggest",
        ]
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in action_keywords)
