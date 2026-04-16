"""
MCP 8: Analytics Agent v2

Improvements:
- Predictive insights (trend detection across modules)
- Cross-module aggregation (pulls data from all 8 MCPs)
- Anomaly detection (flags unusual drops/spikes)
- Actionable recommendations ranked by ROI
- Cohort comparison (this week vs last week)
- Health score per module (0-100)
"""
import json
from agents.base_agent import BaseMCPAgent
from agents.prompt_templates import SYSTEM_PROMPTS
from database import models
from sqlalchemy import func
from datetime import datetime, timedelta


class AnalyticsAgent(BaseMCPAgent):
    MODULE_NAME = "analytics"

    def get_dashboard_metrics(self, user_id: int, days: int = 7) -> dict:
        """
        Aggregate real-time metrics across all 9 MCP modules.
        Includes week-over-week comparison for trend detection.
        """
        since = datetime.utcnow() - timedelta(days=days)
        prev_since = datetime.utcnow() - timedelta(days=days * 2)

        # ── Tasks ──────────────────────────────────────────────────────
        def task_count(status=None, since_dt=None, owner=user_id):
            q = self.db.query(func.count(models.Task.id)).filter_by(owner_id=owner)
            if status:
                q = q.filter(models.Task.status == status)
            if since_dt:
                q = q.filter(models.Task.created_at >= since_dt)
            return q.scalar() or 0

        total_tasks     = task_count()
        done_tasks      = task_count(status=models.TaskStatus.done)
        done_this_period = task_count(status=models.TaskStatus.done, since_dt=since)
        done_prev_period = task_count(status=models.TaskStatus.done, since_dt=prev_since) - done_this_period
        overdue_tasks = (
            self.db.query(func.count(models.Task.id))
            .filter(
                models.Task.owner_id == user_id,
                models.Task.due_date < datetime.utcnow(),
                models.Task.status != models.TaskStatus.done,
            ).scalar() or 0
        )

        # ── Content ────────────────────────────────────────────────────
        total_content   = self.db.query(func.count(models.ContentPost.id)).filter_by(owner_id=user_id).scalar() or 0
        published       = self.db.query(func.count(models.ContentPost.id)).filter_by(owner_id=user_id, status=models.ContentStatus.published).scalar() or 0
        content_this    = self.db.query(func.count(models.ContentPost.id)).filter(models.ContentPost.owner_id == user_id, models.ContentPost.created_at >= since).scalar() or 0

        # ── CRM / Leads ────────────────────────────────────────────────
        total_leads     = self.db.query(func.count(models.Lead.id)).filter_by(owner_id=user_id).scalar() or 0
        new_leads       = self.db.query(func.count(models.Lead.id)).filter(models.Lead.owner_id == user_id, models.Lead.created_at >= since).scalar() or 0
        new_leads_prev  = self.db.query(func.count(models.Lead.id)).filter(models.Lead.owner_id == user_id, models.Lead.created_at >= prev_since, models.Lead.created_at < since).scalar() or 0
        won_leads       = self.db.query(func.count(models.Lead.id)).filter_by(owner_id=user_id, status=models.LeadStatus.won).scalar() or 0
        pipeline_value  = self.db.query(func.sum(models.Lead.deal_value)).filter(models.Lead.owner_id == user_id, models.Lead.status != models.LeadStatus.lost).scalar() or 0

        # ── Social ─────────────────────────────────────────────────────
        scheduled_posts = self.db.query(func.count(models.SocialPost.id)).filter_by(owner_id=user_id, status="scheduled").scalar() or 0
        published_posts = self.db.query(func.count(models.SocialPost.id)).filter_by(owner_id=user_id, status="published").scalar() or 0

        # ── SEO ────────────────────────────────────────────────────────
        total_keywords  = self.db.query(func.count(models.SEOKeyword.id)).filter_by(owner_id=user_id).scalar() or 0
        broken_links    = self.db.query(func.count(models.BrokenLink.id)).filter_by(owner_id=user_id, is_fixed=False).scalar() or 0

        # ── YouTube ────────────────────────────────────────────────────
        total_videos    = self.db.query(func.count(models.YouTubeVideo.id)).filter_by(owner_id=user_id).scalar() or 0
        draft_videos    = self.db.query(func.count(models.YouTubeVideo.id)).filter_by(owner_id=user_id, status="draft").scalar() or 0

        # ── Activity events this period ────────────────────────────────
        event_counts = (
            self.db.query(models.AnalyticsEvent.module, func.count(models.AnalyticsEvent.id))
            .filter(models.AnalyticsEvent.user_id == user_id, models.AnalyticsEvent.timestamp >= since)
            .group_by(models.AnalyticsEvent.module)
            .all()
        )
        module_activity = {row[0]: row[1] for row in event_counts}

        # ── Week-over-week deltas ───────────────────────────────────────
        def delta(current, previous):
            if previous == 0:
                return None
            return round(((current - previous) / previous) * 100, 1)

        return {
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat(),
            "tasks": {
                "total": total_tasks,
                "completed": done_tasks,
                "completed_this_period": done_this_period,
                "overdue": overdue_tasks,
                "completion_rate": round((done_tasks / max(total_tasks, 1)) * 100, 1),
                "wow_delta": delta(done_this_period, done_prev_period),
            },
            "content": {
                "total": total_content,
                "published": published,
                "created_this_period": content_this,
                "publish_rate": round((published / max(total_content, 1)) * 100, 1),
            },
            "crm": {
                "total_leads": total_leads,
                "new_leads": new_leads,
                "won": won_leads,
                "pipeline_value": round(pipeline_value, 2),
                "conversion_rate": round((won_leads / max(total_leads, 1)) * 100, 1),
                "wow_delta": delta(new_leads, new_leads_prev),
            },
            "social": {
                "scheduled": scheduled_posts,
                "published": published_posts,
            },
            "seo": {
                "total_keywords": total_keywords,
                "broken_links": broken_links,
            },
            "youtube": {
                "total_videos": total_videos,
                "drafts": draft_videos,
            },
            "module_activity": module_activity,
        }

    def compute_module_health_scores(self, metrics: dict) -> dict:
        """
        Score each module 0-100 based on usage and output quality signals.
        """
        scores = {}

        # Tasks health: completion rate + no overdue
        task_m = metrics.get("tasks", {})
        task_score = task_m.get("completion_rate", 0)
        if task_m.get("overdue", 0) > 3:
            task_score -= 20
        scores["task"] = max(0, min(100, round(task_score)))

        # Content health: publish rate + recent activity
        content_m = metrics.get("content", {})
        content_score = content_m.get("publish_rate", 0)
        if content_m.get("created_this_period", 0) > 0:
            content_score += 20
        scores["content"] = max(0, min(100, round(content_score)))

        # CRM health: conversion + active pipeline
        crm_m = metrics.get("crm", {})
        crm_score = crm_m.get("conversion_rate", 0) * 2
        if crm_m.get("new_leads", 0) > 0:
            crm_score += 20
        if crm_m.get("pipeline_value", 0) > 0:
            crm_score += 20
        scores["crm"] = max(0, min(100, round(crm_score)))

        # SEO health: keywords tracked + broken links resolved
        seo_m = metrics.get("seo", {})
        seo_score = 60 if seo_m.get("total_keywords", 0) > 10 else 30
        if seo_m.get("broken_links", 0) > 5:
            seo_score -= 20
        scores["seo"] = max(0, min(100, round(seo_score)))

        # Social health: posts scheduled
        social_m = metrics.get("social", {})
        social_score = 80 if social_m.get("scheduled", 0) > 5 else (
            50 if social_m.get("scheduled", 0) > 0 else 20
        )
        scores["social"] = social_score

        # YouTube health
        yt_m = metrics.get("youtube", {})
        yt_score = 70 if yt_m.get("total_videos", 0) > 3 else (
            40 if yt_m.get("total_videos", 0) > 0 else 20
        )
        scores["youtube"] = yt_score

        overall = round(sum(scores.values()) / max(len(scores), 1))
        scores["overall"] = overall
        return scores

    def detect_anomalies(self, metrics: dict) -> list[dict]:
        """Flag unusual patterns that need attention."""
        anomalies = []

        tasks = metrics.get("tasks", {})
        if tasks.get("overdue", 0) > 5:
            anomalies.append({
                "module": "tasks",
                "severity": "high",
                "issue": f"{tasks['overdue']} overdue tasks",
                "action": "Review and reschedule or complete overdue tasks",
            })

        crm = metrics.get("crm", {})
        wow = crm.get("wow_delta")
        if wow is not None and wow < -30:
            anomalies.append({
                "module": "crm",
                "severity": "medium",
                "issue": f"Lead acquisition dropped {abs(wow)}% vs last period",
                "action": "Check lead sources and increase outreach activity",
            })

        seo = metrics.get("seo", {})
        if seo.get("broken_links", 0) > 10:
            anomalies.append({
                "module": "seo",
                "severity": "high",
                "issue": f"{seo['broken_links']} unfixed broken links",
                "action": "Run redirect suggestions and fix broken links immediately",
            })

        return anomalies

    async def generate_weekly_report(self, user_id: int) -> dict:
        """
        AI-powered weekly report with predictive recommendations.
        """
        current = self.get_dashboard_metrics(user_id, days=7)
        health  = self.compute_module_health_scores(current)
        anomalies = self.detect_anomalies(current)

        prompt = f"""Generate a comprehensive weekly business report:

Period metrics (last 7 days):
{json.dumps(current, indent=2, default=str)}

Module health scores: {json.dumps(health)}
Anomalies detected: {json.dumps(anomalies)}

Report structure:
1. Executive summary (3 sentences — what happened, what's good, what needs attention)
2. Top 3 wins this week (specific, with numbers)
3. Top 3 problems (specific, with root cause hypothesis)
4. Predictive insight: based on trends, what will happen next week if nothing changes?
5. Priority actions for next week (ranked by ROI)
6. One bold strategic recommendation

Tone: direct, data-driven, like a trusted advisor not a bot."""

        insights = await self.ai.generate(
            self.inject_context(prompt), self.system_prompt,
            temperature=0.6, max_tokens=1500
        )

        # Save report to DB
        report = models.WeeklyReport(
            week_start=datetime.utcnow() - timedelta(days=7),
            week_end=datetime.utcnow(),
            report_data={**current, "health": health, "anomalies": anomalies},
            ai_insights=insights,
            owner_id=user_id,
        )
        self.db.add(report)
        self.db.commit()

        self.track_event("weekly_report_generated")
        return {
            "metrics": current,
            "health_scores": health,
            "anomalies": anomalies,
            "ai_insights": insights,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def get_module_insights(self, module: str, data: dict) -> str:
        """Targeted AI insight for a single module's data."""
        prompt = f"""Analyze this {module} module data and give 3 specific, numbered insights:

{json.dumps(data, indent=2, default=str)}

Each insight must:
- Reference a specific number from the data
- Explain the implication (not just the number)
- Suggest one concrete action

Be terse and direct. No fluff."""
        return await self.ai.generate(
            prompt, self.system_prompt, temperature=0.5, max_tokens=600
        )

    def get_activity_timeline(self, user_id: int, limit: int = 20) -> list[dict]:
        """Return recent activity logs formatted for the timeline UI."""
        logs = (
            self.db.query(models.ActivityLog)
            .filter_by(user_id=user_id)
            .order_by(models.ActivityLog.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": log.id,
                "action": log.action,
                "module": log.module,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "timestamp": log.created_at.isoformat(),
            }
            for log in logs
        ]
