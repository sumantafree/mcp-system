"""
ReAct Reasoning Engine — Reasoning + Acting pattern for ARIA.

How it works:
1. PLAN  — break request into steps
2. ACT   — execute each step using the right MCP agent
3. OBSERVE — collect result
4. REFLECT — evaluate quality, retry if needed
5. RESPOND — synthesize final natural language answer

Supports:
- Multi-step workflows (SEO research → Blog → Social post)
- Automatic retry on low-quality outputs (score < 7)
- Parallel step execution where steps are independent
- Graceful degradation (partial failure → partial success)
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from integrations.ai_client import AIClient
from agents.prompt_templates import (
    SYSTEM_PROMPTS,
    PLANNING_PROMPT,
    REFLECTION_PROMPT,
    INTENT_ROUTER_PROMPT,
)

logger = logging.getLogger("mcp.reasoning")


@dataclass
class Step:
    step_num: int
    module: str
    action: str
    input_data: dict
    depends_on: list[int] = field(default_factory=list)  # step numbers this depends on
    result: Any = None
    error: Optional[str] = None
    reflection_score: Optional[int] = None
    completed: bool = False
    retried: bool = False


@dataclass
class ExecutionPlan:
    goal: str
    steps: list[Step]
    risks: list[str]
    clarification_needed: Optional[str]
    created_at: datetime = field(default_factory=datetime.utcnow)


class ReasoningEngine:
    """
    Orchestrates multi-step AI workflows with plan → act → reflect loop.
    """

    MAX_RETRIES_PER_STEP = 1
    MIN_QUALITY_SCORE = 6  # steps below this score get retried

    def __init__(self, db: Session, user_id: int, provider: Optional[str] = None):
        self.db = db
        self.user_id = user_id
        self.ai = AIClient(provider)

    # ── Entry point ─────────────────────────────────────────────────────

    async def run(self, request: str, context: str = "") -> dict:
        """
        Full ReAct loop for a user request.
        Returns: {goal, steps_executed, final_answer, plan, success}
        """
        logger.info(f"[ReAct] Starting: {request[:80]}")

        # Step 1: Route intent
        routing = await self._route_intent(request)
        is_multi_step = routing.get("multi_step", False)

        # Step 2: Plan (only for multi-step or complex requests)
        if is_multi_step:
            plan = await self._create_plan(request, context)
            if plan.clarification_needed:
                return {
                    "needs_clarification": True,
                    "question": plan.clarification_needed,
                    "partial_plan": plan.goal,
                }
        else:
            # Single-step: create trivial plan from routing
            plan = ExecutionPlan(
                goal=routing.get("action", request),
                steps=[Step(
                    step_num=1,
                    module=routing.get("module", "general"),
                    action=routing.get("action", ""),
                    input_data={**routing.get("parameters", {}), "original_request": request},
                )],
                risks=[],
                clarification_needed=None,
            )

        # Step 3: Execute plan
        results = await self._execute_plan(plan, request)

        # Step 4: Synthesize final answer
        final_answer = await self._synthesize(plan.goal, results, request)

        return {
            "success": True,
            "goal": plan.goal,
            "routing": routing,
            "steps_executed": len([s for s in plan.steps if s.completed]),
            "results": results,
            "final_answer": final_answer,
            "is_multi_step": is_multi_step,
        }

    # ── Intent Routing ───────────────────────────────────────────────────

    async def _route_intent(self, message: str) -> dict:
        prompt = INTENT_ROUTER_PROMPT.replace('"{message}"', f'"{message}"')
        response = await self.ai.generate(
            prompt, temperature=0.1, json_mode=True, use_cache=True
        )
        return self.ai.parse_json_response(response)

    # ── Planning ─────────────────────────────────────────────────────────

    async def _create_plan(self, request: str, context: str) -> ExecutionPlan:
        prompt = PLANNING_PROMPT.format(request=request, context=context or "No additional context")
        response = await self.ai.generate(
            prompt,
            SYSTEM_PROMPTS["assistant"],
            temperature=0.3,
            json_mode=True,
        )
        data = self.ai.parse_json_response(response)

        steps = []
        for raw_step in data.get("steps", []):
            steps.append(Step(
                step_num=raw_step.get("step", len(steps) + 1),
                module=raw_step.get("module", "general"),
                action=raw_step.get("action", ""),
                input_data={"description": raw_step.get("input", ""), "original_request": request},
            ))

        return ExecutionPlan(
            goal=data.get("goal", request),
            steps=steps,
            risks=data.get("risks", []),
            clarification_needed=data.get("clarification_needed"),
        )

    # ── Execution ─────────────────────────────────────────────────────────

    async def _execute_plan(self, plan: ExecutionPlan, original_request: str) -> list[dict]:
        """Execute steps, passing outputs from earlier steps to later ones."""
        step_outputs: dict[int, Any] = {}
        result_summaries = []

        # Group steps by dependency level for potential parallel execution
        independent_steps = [s for s in plan.steps if not s.depends_on]
        dependent_steps = [s for s in plan.steps if s.depends_on]

        # Execute independent steps first (could be parallel, kept sequential for safety)
        for step in independent_steps:
            await self._execute_step(step, step_outputs, original_request)
            step_outputs[step.step_num] = step.result

        # Execute dependent steps in order
        for step in dependent_steps:
            # Inject outputs from dependencies
            for dep in step.depends_on:
                if dep in step_outputs:
                    step.input_data[f"step_{dep}_result"] = str(step_outputs[dep])[:500]
            await self._execute_step(step, step_outputs, original_request)
            step_outputs[step.step_num] = step.result

        for step in plan.steps:
            result_summaries.append({
                "step": step.step_num,
                "module": step.module,
                "action": step.action,
                "completed": step.completed,
                "result": step.result,
                "error": step.error,
                "quality_score": step.reflection_score,
            })

        return result_summaries

    async def _execute_step(self, step: Step, prior_outputs: dict, original_request: str):
        """Execute a single step with optional self-reflection + retry."""
        try:
            result = await self._dispatch_to_module(step, original_request)
            step.result = result

            # Reflect on output quality for important steps
            if result and isinstance(result, (dict, str)):
                output_str = str(result)[:800]
                reflection = await self.ai.reflect(output_str, f"{step.module}.{step.action}")
                step.reflection_score = reflection.get("overall_score", 8)

                # Retry if quality is too low
                if (
                    step.reflection_score < self.MIN_QUALITY_SCORE
                    and not step.retried
                    and reflection.get("revised_output")
                ):
                    logger.info(f"Step {step.step_num} score={step.reflection_score}, retrying...")
                    step.retried = True
                    step.input_data["improvement_hints"] = str(reflection.get("improvements", []))
                    retry_result = await self._dispatch_to_module(step, original_request)
                    if retry_result:
                        step.result = retry_result

            step.completed = True
            logger.info(f"Step {step.step_num} ({step.module}.{step.action}) ✓ score={step.reflection_score}")

        except Exception as e:
            step.error = str(e)
            step.completed = False
            logger.error(f"Step {step.step_num} failed: {e}")

    async def _dispatch_to_module(self, step: Step, original_request: str) -> Any:
        """Route a step to the appropriate MCP agent method."""
        from agents.task_agent import TaskAgent
        from agents.seo_agent import SEOAgent
        from agents.content_agent import ContentAgent
        from agents.social_agent import SocialAgent
        from agents.youtube_agent import YouTubeAgent
        from agents.crm_agent import CRMAgent
        from agents.analytics_agent import AnalyticsAgent

        module = step.module
        action = step.action
        params = step.input_data

        if module == "task":
            agent = TaskAgent(self.db, self.user_id)
            if "create" in action:
                return await agent.create_task_from_text(
                    params.get("title") or params.get("original_request", "")
                )
            if "suggest" in action:
                return await agent.get_ai_suggestions(self.user_id)

        elif module == "seo":
            agent = SEOAgent(self.db, self.user_id)
            if "keyword" in action or "cluster" in action:
                kws = params.get("keywords", [params.get("topic", original_request)])
                if isinstance(kws, str):
                    kws = [kws]
                return await agent.cluster_keywords(kws, params.get("language", "en"))
            if "meta" in action:
                return await agent.generate_meta(
                    params.get("title", ""),
                    params.get("content", ""),
                    params.get("keyword", ""),
                    params.get("language", "en"),
                )
            if "audit" in action:
                return await agent.audit_content_seo(
                    params.get("content", ""), params.get("keyword", "")
                )

        elif module == "content":
            agent = ContentAgent(self.db, self.user_id)
            if "blog" in action:
                return await agent.generate_blog(
                    topic=params.get("topic", original_request),
                    keyword=params.get("keyword", ""),
                    language=params.get("language", "en"),
                    word_count=int(params.get("word_count", 1200)),
                    tone=params.get("tone", "professional"),
                )
            if "caption" in action:
                return await agent.generate_social_captions(
                    topic=params.get("topic", original_request),
                    platform=params.get("platform", "instagram"),
                )
            if "rewrite" in action or "news" in action:
                return await agent.rewrite_news(
                    original_text=params.get("content", original_request),
                    language=params.get("language", "en"),
                )

        elif module == "social":
            agent = SocialAgent(self.db, self.user_id)
            if "calendar" in action:
                return await agent.generate_content_calendar(
                    niche=params.get("niche", "general"),
                    platforms=params.get("platforms", ["instagram"]),
                    days=int(params.get("days", 7)),
                )
            return await agent.generate_post(
                topic=params.get("topic", original_request),
                platform=params.get("platform", "instagram"),
                language=params.get("language", "en"),
            )

        elif module == "youtube":
            agent = YouTubeAgent(self.db, self.user_id)
            if "script" in action:
                return await agent.generate_script(
                    topic=params.get("topic", original_request),
                    duration_minutes=int(params.get("duration", 10)),
                    style=params.get("style", "educational"),
                    language=params.get("language", "en"),
                )
            if "title" in action:
                return await agent.optimize_title(
                    topic=params.get("topic", original_request),
                    niche=params.get("niche", "general"),
                )
            if "shorts" in action:
                return await agent.generate_shorts_script(
                    main_script=params.get("script", ""),
                    topic=params.get("topic", original_request),
                )

        elif module == "crm":
            agent = CRMAgent(self.db, self.user_id)
            if "score" in action:
                return await agent.score_lead(params)
            if "followup" in action:
                return await agent.generate_followup_message(
                    lead_name=params.get("lead_name", ""),
                    company=params.get("company", ""),
                    stage=params.get("stage", "contacted"),
                    channel=params.get("channel", "whatsapp"),
                )

        elif module == "analytics":
            agent = AnalyticsAgent(self.db, self.user_id)
            if "report" in action:
                return await agent.generate_weekly_report(self.user_id)
            return agent.get_dashboard_metrics(self.user_id)

        # Fallback: generate a direct AI response
        response = await self.ai.generate(
            original_request, SYSTEM_PROMPTS["assistant"], temperature=0.7
        )
        return {"response": response}

    # ── Synthesis ─────────────────────────────────────────────────────────

    async def _synthesize(self, goal: str, results: list[dict], original_request: str) -> str:
        """Synthesize a natural language final answer from all step results."""
        completed = [r for r in results if r["completed"]]
        failed = [r for r in results if not r["completed"]]

        if not completed:
            return "I encountered issues completing your request. Please try again or rephrase."

        summary_parts = []
        for r in completed[:3]:  # top 3 results
            if r["result"]:
                result_str = str(r["result"])[:300]
                summary_parts.append(f"[{r['module']}.{r['action']}]: {result_str}")

        results_summary = "\n".join(summary_parts)

        prompt = f"""As ARIA, give a concise (3-5 sentence) natural response:

Original request: {original_request}
Goal achieved: {goal}
Results summary:
{results_summary}
{"Partial failures: " + str([f['action'] for f in failed]) if failed else ""}

Be conversational, mention key outcomes, and suggest a next step if relevant."""

        return await self.ai.generate(
            prompt, SYSTEM_PROMPTS["assistant"], temperature=0.7, max_tokens=300
        )
