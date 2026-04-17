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

    async def rewrite_news(
        self,
        original_text: str,
        language: str = "en",
        style: str = "news",
    ) -> dict:
        lang_instruction = (
            "Rewrite in Hindi (Devanagari)" if language == "hi" else "Rewrite in English"
        )
        prompt = (
            f"You are a professional news editor. {lang_instruction}.\n\n"
            f"Style: {style}\n\n"
            f"Original article:\n{original_text[:3000]}\n\n"
            "Rewrite this article to be unique, well-structured, and engaging. "
            "Return JSON:\n"
            '{"title": "...", "rewritten_content": "...", "summary": "...", '
            '"key_points": ["..."], "estimated_word_count": number}'
        )
        response = await self.ai.generate(
            prompt,
            self.system_prompt,
            temperature=0.75,
            json_mode=True,
        )
        return self.ai.parse_json_response(response)

    async def generate_social_captions(
        self,
        topic: str,
        platform: str = "instagram",
        language: str = "en",
        count: int = 3,
    ) -> dict:
        lang_instruction = (
            "Write in Hindi" if language == "hi" else "Write in English"
        )
        platform_guidance = {
            "instagram": "Use emojis, line breaks, and 5-10 relevant hashtags.",
            "twitter": "Max 280 characters per caption. Punchy and concise.",
            "linkedin": "Professional tone, no excessive emojis, thought-leadership style.",
            "facebook": "Conversational, shareable, include a call-to-action.",
        }.get(platform, "Engaging and platform-appropriate.")

        prompt = (
            f"Generate {count} unique social media captions for {platform}.\n"
            f"Topic: {topic}\n"
            f"{lang_instruction}. {platform_guidance}\n\n"
            "Return JSON:\n"
            '{"captions": [{"caption": "...", "hashtags": ["..."]}]}'
        )
        response = await self.ai.generate(
            prompt,
            self.system_prompt,
            temperature=0.85,
            json_mode=True,
        )
        return self.ai.parse_json_response(response)

    async def translate_content(
        self,
        content: str,
        target_language: str,
    ) -> str:
        lang_names = {
            "hi": "Hindi (Devanagari script)",
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "ar": "Arabic",
            "pt": "Portuguese",
            "ja": "Japanese",
            "zh": "Chinese (Simplified)",
        }
        lang_name = lang_names.get(target_language, target_language)
        prompt = (
            f"Translate the following content to {lang_name}.\n"
            "Preserve formatting, headings, and meaning exactly.\n"
            "Return ONLY the translated text, no explanations.\n\n"
            f"Content:\n{content[:4000]}"
        )
        return await self.ai.generate(
            prompt,
            temperature=0.3,
            max_tokens=4096,
        )
