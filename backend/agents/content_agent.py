"""
MCP 3: Content Agent v2

Improvements:
- Uses centralized prompt templates (BLOG_GENERATION_PROMPT)
- Receives best keyword from SEO agent via cross-module messaging
- Self-reflection on blog quality before returning
- Receives topic cluster from SEO and auto-suggests spoke content
- Audience persona injection
- Cross-module: publishes blog excerpt → Social agent for captions
- Plagiarism-safety check via uniqueness prompt
"""
import json
from agents.base_agent import BaseMCPAgent
from agents.prompt_templates import SYSTEM_PROMPTS, BLOG_GENERATION_PROMPT
from database import models
from datetime import datetime


class ContentAgent(BaseMCPAgent):
    MODULE_NAME = "content"

    # Audience personas per tone
    AUDIENCE_MAP = {
        "professional":  "business professionals, decision-makers, B2B audience",
        "casual":        "general readers, social media users",
        "educational":   "students, learners, knowledge-seekers",
        "conversational":"everyday consumers, friendly tone expected",
        "technical":     "developers, engineers, technical practitioners",
    }

    async def generate_blog(
        self,
        topic: str,
        keyword: str,
        language: str = "en",
        word_count: int = 1200,
        tone: str = "professional",
    ) -> dict:
        """
        Generate SEO blog using the centralized template.
        Checks for a better keyword from SEO agent first.
        Self-reflects on quality before returning.
        """
        # Pick up SEO agent's keyword recommendation if available
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

        # Self-reflect: check quality score
        blog_content = result.get("content", "")
        if blog_content and len(blog_content) > 500:
            reflection = await self.ai.reflect(
                blog_content[:1000],
                f"SEO blog about '{topic}' targeting keyword '{keyword}'"
            )
            result["quality_score"] = reflection.get("overall_score", 8)
            result["quality_issues"] = reflection.get("issues", [])

            # If quality is low, regenerate the intro and conclusion
            if reflection.get("overall_score", 8) < 6:
                improved = await self._improve_weak_sections(
                    result, topic, keyword, reflection.get("improvements", [])
                )
                result.update(improved)
                result["was_improved"] = True

        # Cross-module: send excerpt to Social agent for caption generation
        excerpt = result.get("excerpt") or blog_content[:200]
        self.send_to_agent("social", "blog_published", json.dumps({
            "title": result.get("title", topic),
            "excerpt": excerpt,
            "keyword": keyword,
            "tags": result.get("tags", []),
        }))

        self.track_event("blog_generated", {
            "topic": topic,
            "language": language,
            "word_count": result.get("word_count", word_count),
            "quality_score": result.get("quality_score"),
        })
        return result

    async def _improve_weak_sections(
        self, result: dict, topic: str, keyword: str, improvements: list
    ) -> dict:
        """Regenerate weak intro and conclusion based on reflection feedback."""
        improvement_hints = "; ".join(improvements[:3])
        prompt = f"""Rewrite only the introduction and conclusion of this blog:

Topic: {topic} | Keyword: {keyword}
Current intro (first 300 chars): {result.get('content', '')[:300]}
Issues to fix: {improvement_hints}

Return JSON:
{{
  "improved_intro": "new 100-150 word introduction with hook + keyword",
  "improved_conclusion": "new 80-100 word conclusion with CTA"
}}"""
        resp = await self.ai.generate(prompt, self.system_prompt, temperature=0.8, json_mode=True)
        return self.ai.parse_json_response(resp)

    async def rewrite_news(
        self, original_text: str, language: str = "en", style: str = "news"
    ) -> dict:
        """
        Rewrite news with uniqueness assurance and source attribution removal.
        """
        lang_note = "Rewrite in Hindi (Devanagari)" if language == "hi" else "Rewrite in English"

        style_guides = {
            "news":        "journalistic, inverted pyramid structure, factual",
            "blog":        "conversational, opinionated, first-person friendly",
            "social":      "punchy, shareable, 3-4 key points as bullets",
            "newsletter":  "warm, curated feel, adds editor commentary",
        }
        style_instruction = style_guides.get(style, style)

        prompt = f"""{lang_note} in {style} style ({style_instruction}).

Original article ({len(original_text)} chars):
{original_text[:2500]}

Requirements:
- Change sentence structure throughout (no copied phrases)
- Preserve all facts and figures exactly
- Add a fresh angle or insight not in the original
- Remove any attribution to original source
- If any quotes exist, paraphrase them

Return JSON:
{{
  "title": "new headline",
  "rewritten_content": "full rewritten article",
  "summary": "2-3 sentence summary",
  "key_points": ["point1", "point2", "point3"],
  "fresh_angle": "what new insight was added",
  "estimated_uniqueness": "x%"
}}"""

        response = await self.ai.generate(
            prompt, self.system_prompt, temperature=0.9, max_tokens=3000, json_mode=True
        )
        result = self.ai.parse_json_response(response)
        self.track_event("news_rewritten", {"language": language, "style": style})
        return result

    async def generate_social_captions(
        self,
        topic: str,
        platform: str,
        language: str = "en",
        count: int = 3,
        brand_voice: str = "",
    ) -> dict:
        """
        Generate platform-native captions.
        Picks up blog context from cross-module messaging if available.
        """
        # Check if social agent sent back any trend context
        blog_context = self.receive_from_agent("seo", "best_keyword")

        platform_specs = {
            "instagram": {
                "max_chars": 2200, "style": "visual storytelling, emojis welcome",
                "hook": "Start with a bold statement or question",
                "cta": "Save this post / Tag someone",
            },
            "twitter":  {
                "max_chars": 280, "style": "punchy, witty, no hashtags in body",
                "hook": "Lead with the most surprising fact",
                "cta": "Retweet if you agree",
            },
            "linkedin": {
                "max_chars": 1300, "style": "professional insight, thought leadership",
                "hook": "Start with a counterintuitive observation",
                "cta": "What's your experience? Comment below",
            },
            "facebook": {
                "max_chars": 800, "style": "conversational, community-driven",
                "hook": "Ask a relatable question",
                "cta": "Share with someone who needs this",
            },
            "youtube":  {
                "max_chars": 5000, "style": "description with timestamps and keywords",
                "hook": "Describe what viewer will learn",
                "cta": "Subscribe and hit the bell",
            },
        }

        spec = platform_specs.get(platform, {
            "max_chars": 500, "style": "engaging", "hook": "Bold opener", "cta": "Learn more"
        })
        lang_note = "Write in Hindi" if language == "hi" else "Write in English"

        prompt = f"""{lang_note}. Create {count} {platform} captions about: "{topic}"

Platform rules:
- Max chars: {spec['max_chars']}
- Style: {spec['style']}
- Hook formula: {spec['hook']}
- CTA formula: {spec['cta']}
{"Brand voice context: " + brand_voice if brand_voice else ""}
{"Related content: " + blog_context[:100] if blog_context else ""}

Each caption must be distinct — different angles, different hooks.

Return JSON:
{{
  "captions": [
    {{
      "caption": "full caption text",
      "hashtags": ["#tag1", "#tag2", "#tag3"],
      "hook_type": "question|stat|story|controversy|how-to",
      "char_count": number,
      "best_post_time": "day + time",
      "predicted_engagement": "low|medium|high"
    }}
  ],
  "best_caption_index": 0,
  "posting_strategy": "how to use all {count} captions"
}}"""

        response = await self.ai.generate(
            prompt, self.system_prompt, temperature=0.9, json_mode=True
        )
        result = self.ai.parse_json_response(response)
        self.track_event("captions_generated", {"platform": platform, "count": count})
        return result

    async def translate_content(self, content: str, target_language: str) -> dict:
        """
        Translate content with SEO preservation and quality check.
        Returns translated text + quality notes.
        """
        lang_map = {
            "hi": "Hindi (Devanagari script)",
            "en": "English",
            "mr": "Marathi (Devanagari script)",
            "ta": "Tamil",
            "te": "Telugu",
            "bn": "Bengali",
        }
        target = lang_map.get(target_language, target_language)

        prompt = f"""Translate to {target}. Preserve ALL of the following:
- Heading structure (H1, H2, H3 hierarchy)
- HTML tags if present
- SEO keyword intent (use natural equivalents, not literal translations)
- Paragraph breaks and formatting
- Lists and bullet points

Source content:
{content[:4000]}

Return JSON:
{{
  "translated_content": "full translation",
  "target_language": "{target}",
  "keywords_translated": {{"original": "translation"}},
  "quality_notes": "any translation challenges or decisions made"
}}"""

        response = await self.ai.generate(
            prompt, self.system_prompt, temperature=0.3, max_tokens=4096, json_mode=True
        )
        result = self.ai.parse_json_response(response)
        self.track_event("content_translated", {"target": target_language})
        return result

    async def generate_content_brief(self, topic: str, keyword: str, competitors: list[str] = None) -> dict:
        """
        Generate a detailed content brief before writing.
        Checks for SEO cluster context from SEO agent.
        """
        cluster_data = self.receive_from_agent("seo", "topic_cluster")
        cluster_context = f"\nSEO cluster context: {cluster_data[:400]}" if cluster_data else ""

        competitor_str = "\n".join(f"- {c}" for c in (competitors or [])[:5])

        prompt = f"""Create a detailed content brief:

Topic: {topic}
Primary Keyword: {keyword}
{cluster_context}
{"Competitor angles to beat:\n" + competitor_str if competitor_str else ""}

Return JSON:
{{
  "recommended_title": "...",
  "target_word_count": number,
  "target_audience": "...",
  "search_intent": "informational|commercial|transactional",
  "outline": [
    {{"heading": "H2 section", "points": ["bullet 1", "bullet 2"], "word_target": 200}}
  ],
  "must_include": ["fact or statistic to include"],
  "must_avoid": ["topic or claim to avoid"],
  "internal_link_targets": ["related topic to link to"],
  "estimated_rank_difficulty": "low|medium|high",
  "unique_angle": "what makes this piece stand out from existing content"
}}"""

        response = await self.ai.generate(
            self.inject_context(prompt), self.system_prompt,
            temperature=0.6, max_tokens=3000, json_mode=True
        )
        self.track_event("content_brief_generated", {"topic": topic})
        return self.ai.parse_json_response(response)
