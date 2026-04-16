"""
MCP 3: Content Agent v2
"""
import json
from agents.base_agent import BaseMCPAgent
from agents.prompt_templates import BLOG_GENERATION_PROMPT
from database import models
from datetime import datetime


class ContentAgent(BaseMCPAgent):
    MODULE_NAME = "content"

    AUDIENCE_MAP = {
        "professional": "business professionals, decision-makers, B2B audience",
        "casual": "general readers, social media users",
        "educational": "students, learners",
        "conversational": "everyday consumers",
        "technical": "developers and engineers",
    }

    async def generate_blog(
        self,
        topic: str,
        keyword: str,
        language: str = "en",
        word_count: int = 1200,
        tone: str = "professional",
    ) -> dict:

        lang_instruction = (
            "Write in Hindi (Devanagari)"
            if language == "hi"
            else "Write in English"
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
            prompt,
            self.system_prompt,
            temperature=0.8,
            json_mode=True,
        )

        return self.ai.parse_json_response(response)

    async def generate_content_brief(
        self,
        topic: str,
        keyword: str,
        competitors: list[str] = None
    ) -> dict:

        # Safe cluster context
        cluster_data = self.receive_from_agent("seo", "topic_cluster")
        if cluster_data:
            cluster_context = "\nSEO cluster context: " + str(cluster_data)[:400]
        else:
            cluster_context = ""

        # Safe competitor string
        competitor_str = ""
        if competitors:
            competitor_str = "\n".join("- " + c for c in competitors[:5])

        # ✅ SAFE FIX (NO f-string backslash issue)
        competitor_text = ""
        if competitor_str:
            competitor_text = "Competitor angles to beat:\n" + competitor_str

        # ✅ CLEAN PROMPT (NO BACKSLASH INSIDE {})
        prompt = (
            "Create a detailed content brief:\n\n"
            f"Topic: {topic}\n"
            f"Primary Keyword: {keyword}\n"
            f"{cluster_context}\n"
            f"{competitor_text}\n\n"
            "Return JSON:\n"
            "{\n"
            '  "recommended_title": "...",\n'
            '  "target_word_count": number,\n'
            '  "target_audience": "...",\n'
            '  "search_intent": "informational|commercial|transactional",\n'
            '  "outline": [\n'
            '    {"heading": "H2", "points": ["point1"], "word_target": 200}\n'
            "  ],\n"
            '  "must_include": ["fact"],\n'
            '  "must_avoid": ["avoid"],\n'
            '  "internal_link_targets": ["topic"],\n'
            '  "estimated_rank_difficulty": "low|medium|high",\n'
            '  "unique_angle": "angle"\n'
            "}"
        )

        response = await self.ai.generate(
            prompt,
            self.system_prompt,
            temperature=0.6,
            json_mode=True,
        )

        return self.ai.parse_json_response(response)
