"""
MCP Agent Registry
Provides a single import point and the pipeline factory.
"""
from agents.task_agent      import TaskAgent
from agents.seo_agent       import SEOAgent
from agents.content_agent   import ContentAgent
from agents.social_agent    import SocialAgent
from agents.youtube_agent   import YouTubeAgent
from agents.crm_agent       import CRMAgent
from agents.website_agent   import WebsiteAgent
from agents.analytics_agent import AnalyticsAgent
from agents.personal_agent  import PersonalAgent
from agents.reasoning_engine import ReasoningEngine

MODULE_REGISTRY = {
    "task":      TaskAgent,
    "seo":       SEOAgent,
    "content":   ContentAgent,
    "social":    SocialAgent,
    "youtube":   YouTubeAgent,
    "crm":       CRMAgent,
    "website":   WebsiteAgent,
    "analytics": AnalyticsAgent,
    "assistant": PersonalAgent,
}


def get_agent(module_name: str, db, user_id: int):
    """Instantiate an agent by module name."""
    cls = MODULE_REGISTRY.get(module_name)
    if not cls:
        raise ValueError(f"Unknown module: {module_name}. Available: {list(MODULE_REGISTRY)}")
    return cls(db, user_id)


# ── Pre-built cross-module pipelines ────────────────────────────────────────

async def run_seo_to_content_pipeline(db, user_id: int, topic: str, keywords: list) -> dict:
    """SEO cluster → best keyword → generate blog → notify Social agent."""
    seo     = SEOAgent(db, user_id)
    content = ContentAgent(db, user_id)

    cluster  = await seo.cluster_keywords(keywords)
    clusters = cluster.get("clusters", [])
    best_kw  = clusters[0].get("primary_keyword", keywords[0]) if clusters else keywords[0]

    blog = await content.generate_blog(topic=topic, keyword=best_kw)
    return {
        "pipeline": "seo_to_content",
        "keyword_used": best_kw,
        "cluster_count": len(clusters),
        "blog": blog,
    }


async def run_content_to_social_pipeline(
    db, user_id: int, blog_title: str, platforms: list
) -> dict:
    """Blog title → generate platform-native posts for each platform."""
    social = SocialAgent(db, user_id)
    posts  = {p: await social.generate_post(topic=blog_title, platform=p) for p in platforms}
    return {"pipeline": "content_to_social", "source": blog_title, "posts": posts}


async def run_crm_auto_followup_pipeline(db, user_id: int) -> dict:
    """Check due follow-ups → generate messages (no auto-send)."""
    crm = CRMAgent(db, user_id)
    due = await crm.auto_sequence_check(user_id)
    results = []
    for item in due[:5]:
        msg = await crm.generate_followup_message(
            lead_name=item["name"],
            company=item.get("company", ""),
            stage=item["stage"],
            channel=item["channel"],
            sequence_number=item["sequence_number"],
        )
        results.append({
            "lead_id":          item["lead_id"],
            "lead_name":        item["name"],
            "channel":          item["channel"],
            "generated_message": msg.get("message"),
            "quality_score":    msg.get("quality_score"),
            "ready_to_send":    (msg.get("quality_score") or 0) >= 7,
        })
    return {
        "pipeline": "crm_auto_followup",
        "due_count": len(due),
        "generated": len(results),
        "items": results,
    }
