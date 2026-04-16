"""
MCP 3: Content Agent v2
"""
import json
from agents.base_agent import BaseMCPAgent
from agents.prompt_templates import SYSTEM_PROMPTS, BLOG_GENERATION_PROMPT
from database import models
from datetime import datetime


class ContentAgent(BaseMCPAgent):
    MODULE_NAME = "content"

    AUDIENCE_MAP = {
        "professional": "business professionals, decision-makers, B2B audience",
        "casual": "general readers, social media users",
        "educational": "students, learners, knowledge-seekers",
        "conversational": "everyday consumers, friendly tone expected",
        "technical": "developers, engineers, technical practitioners",
    }

    async def generate_blog(
        self,
        topic: str,
        keyword: str,
        language: str = "en",
        word_count: int = 1200,
        tone: str = "professional",
    ) -> dict:

        seo_keyword_data = self.receive_from_agent("seo", "best_keyword")
        if seo_keyword_data and not keyword:
            seo_kw = json.loads(seo_keyword_data)
            keyword = seo_kw.get("keyword", keyword)

        lang_instruction = (
            "Write the ENTIRE blog post in Hindi (Devanagari script). "
            "Use natural Hindi writing style, not translated English."
            if language == "hi"
            else "Write in clear, engaging English."
        )

        audience = self.AUDIENCE_MAP.get(tone, "general audience")

        prompt = BLOG_GENERATION_PROMPT.format(
            language_instruction=lang_instruction,
            word_count=word_count,
            topic=topic,
            keyword=keyword,
            tone=tone,
            audience=audience,
        )

        response = await self.ai.generate(
            self.inject_context(prompt),
            self.system_prompt,
            temperature=0.8,
            max_tokens=4096,
            json_mode=True,
        )

        result = self.ai.parse_json_response(response)

        blog_content = result.get("content", "")
        if blog_content and len(blog_content) > 500:
            reflection = await self.ai.reflect(
                blog_content[:1000],
                f"SEO blog about '{topic}' targeting keyword '{keyword}'"
            )
            result["quality_score"] = reflection.get("overall_score", 8)
            result["quality_issues"] = reflection.get("issues", [])

        return result

    async def generate_content_brief(
        self, topic: str, keyword: str, competitors: list[str] = None
    ) -> dict:

        cluster_data = self.receive_from_agent("seo", "topic_cluster")
        cluster_context = f"\nSEO cluster context: {cluster_data[:400]}" if cluster_data else ""

        competitor_str = "\n".join(f"- {c}" for c in (competitors or [])[:5])

        # ✅ FIXED PART (no \n inside f-string expression)
        competitor_text = f"Competitor angles to beat:\n{competitor_str}" if competitor_str else ""

        prompt = f"""Create a detailed content brief:

Topic: {topic}
Primary Keyword: {keyword}
{cluster_context}
{competitor_text}

Return JSON:
{{
  "recommended_title": "...",
  "target_word_count": number,
  "target_audience": "...",
  "search_intent": "informational|commercial|transactional",
  "outline": [
    {{"heading": "H2 section", "points": ["bullet 1", "bullet 2"], "word_target": 200}}
  ],
  "must_include": ["fact"],
  "must_avoid": ["avoid"],
  "internal_link_targets": ["topic"],
  "estimated_rank_difficulty": "low|medium|high",
  "unique_angle": "angle"
}}"""

        response = await self.ai.generate(
            self.inject_context(prompt),
            self.system_prompt,
            temperature=0.6,
            max_tokens=3000,
            json_mode=True,
        )

        self.track_event("content_brief_generated", {"topic": topic})

        return self.ai.parse_json_response(response)
