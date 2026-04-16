"""
MCP 1: Task Manager Agent v2

Improvements:
- Few-shot prompt for accurate NLP task parsing
- Eisenhower matrix priority classification
- Context-aware suggestions using conversation history
- Cross-module: notifies CRM when a lead-related task is created
"""
import json
from agents.base_agent import BaseMCPAgent
from agents.prompt_templates import SYSTEM_PROMPTS, TASK_PARSE_PROMPT
from database import models
from datetime import datetime
from typing import Optional


class TaskAgent(BaseMCPAgent):
    MODULE_NAME = "task"

    async def create_task_from_text(self, text: str) -> dict:
        """Parse natural language into a structured task using few-shot prompting."""
        prompt = TASK_PARSE_PROMPT.replace('"{text}"', f'"{text}"')
        response = await self.ai.generate(
            prompt,
            self.system_prompt,
            temperature=0.3,  # low temperature for consistent parsing
            json_mode=True,
            use_cache=False,
        )
        result = self.ai.parse_json_response(response)

        # Self-reflect if result looks weak
        if not result.get("title") or result.get("parse_error"):
            # Fallback: simpler extraction
            fallback = await self.ai.generate(
                f'Extract task title and priority from: "{text}"\nReturn JSON: {{"title": "...", "priority": "medium", "description": "..."}}',
                temperature=0.2,
                json_mode=True,
            )
            result = self.ai.parse_json_response(fallback)

        # Cross-module: share with CRM if task mentions a lead
        lead_keywords = ["lead", "client", "customer", "prospect", "deal", "follow up"]
        if any(kw in text.lower() for kw in lead_keywords):
            self.send_to_agent("crm", "related_task", json.dumps(result))

        self.track_event("task_created_from_text", {"length": len(text)})
        return result

    async def classify_priority(
        self, title: str, description: str, due_date: Optional[str] = None
    ) -> str:
        """
        Classify priority using Eisenhower matrix (urgent+important = urgent).
        """
        prompt = f"""Classify task priority using the Eisenhower matrix:

Task: {title}
Description: {description}
Due: {due_date or 'not set'}

Eisenhower matrix:
- urgent + important → "urgent"
- not urgent + important → "high"
- urgent + not important → "medium"
- not urgent + not important → "low"

Consider: deadlines, business impact, dependencies, consequences of delay.

Think briefly, then respond with ONLY one word: urgent, high, medium, or low"""

        raw = await self.ai.generate(prompt, self.system_prompt, temperature=0.2)
        priority = raw.strip().lower().split()[0]
        return priority if priority in {"urgent", "high", "medium", "low"} else "medium"

    async def get_ai_suggestions(self, user_id: int) -> dict:
        """Suggest next tasks based on history + cross-module context."""
        recent_tasks = (
            self.db.query(models.Task)
            .filter_by(owner_id=user_id)
            .order_by(models.Task.created_at.desc())
            .limit(10)
            .all()
        )
        task_summary = "\n".join([
            f"- [{t.priority.value}] {t.title} — {t.status.value}"
            for t in recent_tasks
        ]) or "No recent tasks."

        overdue = [t for t in recent_tasks if t.due_date and t.due_date < datetime.utcnow() and t.status != models.TaskStatus.done]
        overdue_str = "\n".join([f"- {t.title}" for t in overdue]) or "None"

        # Pull context from CRM if a deal was recently updated
        crm_context = self.recall_shared_memory("last_command") or ""

        prompt = f"""Suggest 3 high-value next tasks for this user:

Recent tasks:
{task_summary}

Overdue tasks:
{overdue_str}

Cross-module context: {crm_context[:200] if crm_context else "None"}

Return JSON:
{{
  "suggestions": [
    {{
      "title": "specific task title",
      "reason": "why this matters now",
      "priority": "urgent|high|medium|low",
      "estimated_hours": number,
      "module_connection": "which MCP module relates to this"
    }}
  ],
  "productivity_tip": "one personalized tip based on their patterns",
  "focus_area": "what they should focus on today"
}}"""
        response = await self.ai.generate(
            self.inject_context(prompt), self.system_prompt, temperature=0.7, json_mode=True
        )
        return self.ai.parse_json_response(response)

    async def generate_daily_briefing(self, tasks: list) -> str:
        """Generate motivating daily briefing using CoT."""
        task_list = "\n".join([
            f"- [{t.get('priority', '?')}] {t['title']} — due {t.get('due_date', 'no date')}"
            for t in tasks[:8]
        ])

        cot = await self.ai.think_then_answer(
            f"What's the optimal task order and strategy for today?\n\nTasks:\n{task_list}",
            self.system_prompt,
        )

        prompt = f"""Write a daily briefing based on this task analysis:
{cot['reasoning'][:400]}

Format: short motivational opener → 3 priority tasks → 1 productivity tip.
Under 120 words. Energetic and direct."""

        return await self.ai.generate(prompt, self.system_prompt, temperature=0.8)

    async def estimate_completion_time(self, task_title: str, description: str) -> dict:
        """AI-powered time estimation with confidence level."""
        prompt = f"""Estimate realistic completion time for:
Task: {task_title}
Details: {description}

Consider: complexity, research needed, dependencies, typical industry benchmarks.

Return JSON:
{{
  "optimistic_hours": number,
  "realistic_hours": number,
  "pessimistic_hours": number,
  "confidence": "high|medium|low",
  "assumptions": ["assumption 1", "assumption 2"],
  "complexity": "simple|medium|complex|very complex"
}}"""
        response = await self.ai.generate(
            prompt, self.system_prompt, temperature=0.3, json_mode=True
        )
        return self.ai.parse_json_response(response)
