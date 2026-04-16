"""
MCP 6: CRM + WhatsApp Agent v2

Improvements:
- Rubric-based lead scoring (company fit + engagement + need + authority)
- Sequence-aware follow-ups (knows which message # this is)
- Pipeline stage prediction with confidence
- Cross-module: picks up task context from task agent
- Reflection on message quality before sending
"""
import json
from agents.base_agent import BaseMCPAgent
from agents.prompt_templates import SYSTEM_PROMPTS, LEAD_SCORING_PROMPT
from integrations.whatsapp_service import send_whatsapp_message
from integrations.email_service import send_email
from database import models
from datetime import datetime
import logging

logger = logging.getLogger("mcp.crm")


class CRMAgent(BaseMCPAgent):
    MODULE_NAME = "crm"

    async def score_lead(self, lead_data: dict) -> dict:
        """Rubric-based lead scoring with reasoning."""
        # Pull interaction history from DB if lead_id present
        interaction_history = []
        lead_id = lead_data.get("id")
        if lead_id:
            messages = (
                self.db.query(models.WhatsAppMessage)
                .filter_by(lead_id=lead_id)
                .order_by(models.WhatsAppMessage.sent_at.desc())
                .limit(5)
                .all()
            )
            interaction_history = [f"[{m.direction}] {m.message[:100]}" for m in messages]

        # Check if task agent shared any related context
        task_context = self.receive_from_agent("task", "related_task")

        prompt = LEAD_SCORING_PROMPT.format(
            lead_data=json.dumps(lead_data, default=str),
            interaction_history="\n".join(interaction_history) or "No interactions yet",
        )
        if task_context:
            prompt += f"\n\nRelated task context: {task_context}"

        response = await self.ai.generate(
            prompt, self.system_prompt, temperature=0.3, json_mode=True
        )
        result = self.ai.parse_json_response(response)

        # Share scoring result with task agent (may need follow-up task)
        self.send_to_agent("task", "high_priority_lead", json.dumps({
            "lead": lead_data.get("name"),
            "score": result.get("score"),
            "action": result.get("recommended_action"),
        }))

        self.track_event("lead_scored", {"lead_id": lead_id, "score": result.get("score")})
        return result

    async def generate_followup_message(
        self,
        lead_name: str,
        company: str,
        stage: str,
        channel: str,
        context: str = "",
        sequence_number: int = 1,
    ) -> dict:
        """
        Generate personalized follow-up, aware of sequence position.
        Sequence 1 = first contact, 2 = check-in, 3 = value add, 4 = breakup
        """
        sequence_guidance = {
            1: "First touch — introduce yourself, lead with value, no ask yet",
            2: "Second touch — reference prior contact, add new insight, soft ask",
            3: "Third touch — share case study or proof, stronger ask",
            4: "Final touch — polite breakup, leave door open, no pressure",
        }.get(sequence_number, "Follow-up — stay helpful, respect their time")

        channel_constraints = {
            "whatsapp": "casual tone, conversational, 2-3 short paragraphs, 1 emoji max, under 200 words",
            "email": "professional, structured with subject line, 200-300 words, clear CTA",
            "sms": "ultra brief, single sentence CTA, under 160 chars",
        }.get(channel, "professional, concise")

        prompt = f"""Write follow-up message #{sequence_number} for:
Name: {lead_name} | Company: {company}
Pipeline stage: {stage}
Channel: {channel} ({channel_constraints})
Sequence guidance: {sequence_guidance}
Context: {context or 'No specific context'}

Requirements:
- Sound human, not templated
- Reference something specific about them if possible
- One clear value statement
- One soft CTA (question, not demand)

Return JSON:
{{
  "subject": "email subject (leave blank for non-email)",
  "message": "the complete message",
  "tone_used": "...",
  "cta": "what you're asking them to do",
  "personalization_hooks": ["what made this personal"],
  "next_sequence_timing": "wait X days before message {sequence_number + 1}"
}}"""

        response = await self.ai.generate(
            prompt, self.system_prompt, temperature=0.8, json_mode=True
        )
        result = self.ai.parse_json_response(response)

        # Self-reflect on message quality
        if result.get("message"):
            reflection = await self.ai.reflect(
                result["message"],
                f"Follow-up message for {stage} stage lead via {channel}"
            )
            result["quality_score"] = reflection.get("overall_score", 8)
            if reflection.get("overall_score", 8) < 6 and reflection.get("revised_output"):
                result["message"] = reflection["revised_output"]
                result["quality_score"] = 7
                result["was_improved"] = True

        self.track_event("followup_generated", {
            "stage": stage,
            "channel": channel,
            "sequence": sequence_number,
        })
        return result

    async def send_followup(
        self, lead_id: int, channel: str, message: str, to: str, name: str = ""
    ) -> dict:
        """Send follow-up and log to DB."""
        if channel == "whatsapp":
            result = await send_whatsapp_message(to, message)
        elif channel == "email":
            html = f"<p style='font-family:Inter,sans-serif;'>{message.replace(chr(10), '<br>')}</p>"
            success = await send_email(to, f"Following up — {name}", html, message)
            result = {"success": success}
        else:
            return {"success": False, "error": f"Unsupported channel: {channel}"}

        # Log message in DB
        msg = models.WhatsAppMessage(
            lead_id=lead_id,
            direction="outbound",
            message=message,
            is_ai_generated=True,
            status="sent" if result.get("success") else "failed",
        )
        self.db.add(msg)
        self.db.commit()

        self.log_activity(
            f"followup_sent_{channel}",
            entity_type="lead",
            entity_id=lead_id,
            details={"to": to, "result": result},
        )
        return result

    async def suggest_pipeline_stage(self, lead_data: dict, interaction_history: list) -> dict:
        """Predict correct pipeline stage with confidence reasoning."""
        history_str = "\n".join([f"- {h}" for h in interaction_history[-5:]]) or "No interactions"

        # Use CoT for stage prediction
        cot = await self.ai.think_then_answer(
            f"""What pipeline stage should this lead be in?

Lead: {lead_data.get('name')} from {lead_data.get('company')}
Current stage: {lead_data.get('status')}
Interactions:
{history_str}""",
            self.system_prompt,
        )

        prompt = f"""Based on this analysis: {cot['reasoning'][:500]}

Return the recommended pipeline stage as JSON:
{{
  "suggested_stage": "new|contacted|qualified|proposal|won|lost",
  "confidence": "high|medium|low",
  "reasoning": "one sentence explanation",
  "next_action": "specific action to take this week",
  "days_to_close_estimate": number or null,
  "risk_of_losing": "low|medium|high"
}}"""
        response = await self.ai.generate(prompt, self.system_prompt, temperature=0.3, json_mode=True)
        return self.ai.parse_json_response(response)

    async def generate_pipeline_report(self, leads: list) -> dict:
        """AI pipeline report with weighted forecast and action items."""
        stage_weights = {
            "new": 0.05, "contacted": 0.15, "qualified": 0.30,
            "proposal": 0.60, "won": 1.0, "lost": 0.0,
        }
        total_pipeline = sum(l.get("deal_value", 0) or 0 for l in leads)
        weighted = sum(
            (l.get("deal_value", 0) or 0) * stage_weights.get(l.get("status", "new"), 0.1)
            for l in leads
        )

        stage_breakdown = {}
        for lead in leads:
            s = lead.get("status", "new")
            if s not in stage_breakdown:
                stage_breakdown[s] = {"count": 0, "value": 0}
            stage_breakdown[s]["count"] += 1
            stage_breakdown[s]["value"] += lead.get("deal_value", 0) or 0

        summary = "\n".join([
            f"- {l.get('name')} | {l.get('status')} | ${l.get('deal_value', 0) or 0:,.0f}"
            for l in leads[:15]
        ])

        prompt = f"""Analyze this sales pipeline and provide strategic insights:

Pipeline: {len(leads)} leads | Total value: ${total_pipeline:,.0f} | Weighted forecast: ${weighted:,.0f}
Stage breakdown: {json.dumps(stage_breakdown)}

Top leads:
{summary}

Return JSON:
{{
  "total_pipeline_value": {total_pipeline},
  "weighted_forecast": {round(weighted)},
  "forecast_confidence": "low|medium|high",
  "win_rate_estimate": "x%",
  "at_risk_leads": ["name - reason"],
  "hot_leads": ["name - why hot"],
  "insights": ["specific insight with number"],
  "this_week_actions": ["action 1", "action 2", "action 3"],
  "revenue_gap_to_target": "context if known"
}}"""
        response = await self.ai.generate(
            self.inject_context(prompt), self.system_prompt, temperature=0.5, json_mode=True
        )
        return self.ai.parse_json_response(response)

    async def auto_sequence_check(self, user_id: int) -> list[dict]:
        """
        Check all leads and identify which ones need follow-up today.
        Returns action items sorted by priority.
        """
        from datetime import timedelta
        due_followups = (
            self.db.query(models.Lead)
            .filter(
                models.Lead.owner_id == user_id,
                models.Lead.status.notin_([models.LeadStatus.won, models.LeadStatus.lost]),
                models.Lead.next_follow_up <= datetime.utcnow(),
            )
            .order_by(models.Lead.ai_score.desc())
            .limit(10)
            .all()
        )

        action_items = []
        for lead in due_followups:
            # Count prior messages
            msg_count = (
                self.db.query(models.WhatsAppMessage)
                .filter_by(lead_id=lead.id, direction="outbound")
                .count()
            )
            action_items.append({
                "lead_id": lead.id,
                "name": lead.name,
                "company": lead.company,
                "stage": lead.status.value,
                "ai_score": lead.ai_score,
                "sequence_number": msg_count + 1,
                "channel": lead.whatsapp and "whatsapp" or "email",
                "overdue_by": str(datetime.utcnow() - lead.next_follow_up) if lead.next_follow_up else None,
            })

        return action_items
