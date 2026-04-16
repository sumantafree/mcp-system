"""
MCP 5: YouTube Agent v2

Improvements:
- CoT for script planning (outline first, then write)
- Retention hook engineering (pattern interrupt, open loop, curiosity gap)
- Platform algorithm awareness (CTR, watch time, AVD)
- Cross-module: receives content brief from Content agent
- Script quality reflection before return
- Competitor title analysis
- End-screen and card placement suggestions
"""
import json
from agents.base_agent import BaseMCPAgent
from agents.prompt_templates import SYSTEM_PROMPTS


class YouTubeAgent(BaseMCPAgent):
    MODULE_NAME = "youtube"

    # Retention engineering formulas
    HOOK_FORMULAS = [
        "Open loop: Ask a question you answer at the END of the video",
        "Bold claim: Make a surprising statement in the first sentence",
        "Pattern interrupt: Say/show something unexpected",
        "Social proof: 'X people did this and got Y result'",
        "Relatability: 'If you've ever felt X, this video is for you'",
    ]

    async def generate_script(
        self,
        topic: str,
        duration_minutes: int = 10,
        style: str = "educational",
        language: str = "en",
    ) -> dict:
        """
        Two-phase script generation: CoT outline → full script.
        Focuses on retention engineering and watch-time optimization.
        """
        lang_note = "Write the ENTIRE script in Hindi (conversational, not formal)" if language == "hi" else "Write in English"

        # Phase 1: CoT planning
        cot = await self.ai.think_then_answer(
            f"""Plan the optimal structure for a {duration_minutes}-minute {style} YouTube video about "{topic}".
Consider: hook type, content arc, mid-roll retention strategies, emotional journey, and strong ending.""",
            self.system_prompt,
        )

        # Phase 2: Full script using the plan
        words_per_minute = 130
        target_words = duration_minutes * words_per_minute

        prompt = f"""{lang_note}. Write a complete YouTube script.

Topic: {topic}
Duration: {duration_minutes} minutes (~{target_words} words)
Style: {style}
Structural plan: {cot['reasoning'][:600]}

RETENTION ENGINEERING REQUIREMENTS:
- Hook (0-30s): Use ONE of: {self.HOOK_FORMULAS[0]}
- Open loop in intro (tease payoff viewers get at end)
- "B-roll callout" at 2-minute mark to re-hook
- Mid-roll retention spike at 50% mark (surprising insight)
- "Stay till the end" callback at 70% mark
- Strong final CTA (subscribe + one specific action)

Return JSON:
{{
  "title_options": ["5 title variations with different formulas"],
  "thumbnail_text": "max 6 words for thumbnail",
  "hook": {{
    "script": "exact words for first 30 seconds",
    "type": "open_loop|bold_claim|pattern_interrupt",
    "retention_strategy": "why this hook works"
  }},
  "intro": "30-60 second intro script",
  "sections": [
    {{
      "timestamp": "0:30",
      "heading": "section title",
      "script": "word-for-word script",
      "b_roll_note": "suggested B-roll or visual",
      "retention_device": "open loop|pattern interrupt|cliffhanger|stat"
    }}
  ],
  "mid_roll_cta": "subscribe/like CTA script at midpoint",
  "outro": "last 30-60 seconds with CTA",
  "end_screen_suggestion": "what to show on end screen",
  "total_word_count": {target_words},
  "key_takeaways": ["viewer learns X", "viewer learns Y"]
}}"""

        response = await self.ai.generate(
            self.inject_context(prompt), self.system_prompt,
            temperature=0.8, max_tokens=4096, json_mode=True
        )
        result = self.ai.parse_json_response(response)

        # Reflect on hook quality specifically
        hook_text = result.get("hook", {}).get("script", "")
        if hook_text:
            reflection = await self.ai.reflect(
                hook_text,
                "YouTube hook for first 30 seconds — must stop scroll and create curiosity"
            )
            result["hook_quality_score"] = reflection.get("overall_score", 7)
            if reflection.get("overall_score", 7) < 6 and reflection.get("revised_output"):
                result["hook"]["script"] = reflection["revised_output"]
                result["hook"]["was_improved"] = True

        self.track_event("script_generated", {
            "topic": topic,
            "duration": duration_minutes,
            "language": language,
        })
        return result

    async def optimize_title(self, topic: str, niche: str) -> dict:
        """
        Generate titles using proven CTR formulas with click-psychology scoring.
        """
        prompt = f"""Generate 10 YouTube titles for: "{topic}" in the {niche} niche.

Apply these proven title formulas:
1. Number list: "X Ways to..."
2. How-to: "How to [Result] Without [Common Pain]"
3. Curiosity gap: "The [Adj] Secret to [Desired Outcome]"
4. Controversy: "Why Everyone Is Wrong About [Topic]"
5. Personal story: "I Tried [X] for [Time] — Here's What Happened"
6. Vs: "[Option A] vs [Option B] — Which Is Better?"
7. Warning: "Stop Doing [X] If You Want [Y]"
8. Beginner: "[Topic] for Beginners (Complete Guide)"
9. Speed: "Learn [X] in [Short Time]"
10. Authority: "Expert Reveals [Topic] Secrets"

For each title score:
- CTR potential (does it create curiosity?)
- SEO value (does it contain searchable keywords?)
- Thumbnail compatibility (can you visualize it?)

Return JSON:
{{
  "titles": [
    {{
      "title": "...",
      "formula": "which formula used",
      "ctr_score": 1-10,
      "seo_score": 1-10,
      "thumbnail_compatibility": 1-10,
      "overall_score": 1-10,
      "thumbnail_text": "3-5 word thumbnail overlay"
    }}
  ],
  "top_pick": "best title",
  "ab_test_pair": ["title A", "title B"],
  "keyword_to_include": "must-have keyword for SEO"
}}"""

        response = await self.ai.generate(
            prompt, self.system_prompt, temperature=0.8, json_mode=True
        )
        result = self.ai.parse_json_response(response)
        self.track_event("titles_optimized", {"topic": topic, "niche": niche})
        return result

    async def generate_shorts_script(self, main_script: str, topic: str) -> dict:
        """
        Extract 3 high-retention Shorts from a main video script.
        Each Short: hook in 3 seconds, value in 45 seconds, CTA in 5 seconds.
        """
        prompt = f"""Extract 3 viral YouTube Shorts from this video:

Topic: {topic}
Main script excerpt: {main_script[:2000]}

Each Short MUST follow this structure:
- Seconds 0-3: HARD HOOK (bold claim or question — no intro)
- Seconds 3-50: ONE insight delivered with clarity and pace
- Seconds 50-60: CTA (follow for more / watch full video)

Shorts that work best: surprising stats, "most people don't know this", step-by-step mini-tutorial

Return JSON:
{{
  "shorts": [
    {{
      "title": "Short title (SEO + curiosity)",
      "hook": "exact words for first 3 seconds",
      "body": "the 45-second main content script",
      "cta": "closing 5-10 seconds",
      "thumbnail_hook": "text overlay for thumbnail",
      "best_time_to_post": "day + time",
      "estimated_retention": "predicted % completion",
      "cross_promote_at": "timestamp in main video to link this Short"
    }}
  ],
  "repurposing_strategy": "how to sequence posting Shorts vs main video"
}}"""

        response = await self.ai.generate(
            prompt, self.system_prompt, temperature=0.85, json_mode=True
        )
        result = self.ai.parse_json_response(response)
        self.track_event("shorts_generated", {"topic": topic, "count": 3})
        return result

    async def generate_description(
        self, title: str, script_summary: str, keywords: list[str]
    ) -> str:
        """
        SEO-optimized description with timestamps, chapters, and keywords.
        """
        kw_str = ", ".join(keywords[:10])
        prompt = f"""Write a YouTube description for:
Title: {title}
Script summary: {script_summary[:400]}
Keywords: {kw_str}

Structure:
1. Hook paragraph (first 125 chars shown before 'Show more') — must contain primary keyword
2. What viewers will learn (3-5 bullet points)
3. Chapters/timestamps (use placeholders like [00:00] Intro)
4. Resources section (placeholder links)
5. Subscribe + social CTA
6. Keyword paragraph (natural sentences using all keywords)
7. Hashtags (3 max at very bottom)

Max 4500 chars. Make the first 125 chars count — that's the preview."""

        description = await self.ai.generate(
            prompt, self.system_prompt, temperature=0.6, max_tokens=2000
        )
        self.track_event("description_generated", {"title": title})
        return description

    async def channel_audit(self, channel_data: dict) -> dict:
        """
        Full channel audit with algorithm health assessment and 90-day growth plan.
        """
        # Use CoT to reason about channel gaps before making recommendations
        cot = await self.ai.think_then_answer(
            f"What are the biggest growth blockers for this YouTube channel and what should they prioritize?\n\nChannel data: {json.dumps(channel_data, default=str)[:800]}",
            self.system_prompt,
        )

        prompt = f"""Based on this channel analysis: {cot['reasoning'][:600]}

Return a complete channel audit as JSON:
{{
  "overall_score": 0-100,
  "algorithm_health": {{
    "ctr_estimate": "x%",
    "avg_view_duration_estimate": "x minutes",
    "upload_consistency": "daily|weekly|irregular",
    "thumbnail_strategy": "strong|weak|inconsistent"
  }},
  "strengths": ["specific strength with evidence"],
  "critical_issues": [
    {{"issue": "...", "impact": "high|medium|low", "fix": "specific action"}}
  ],
  "content_gaps": ["topic your audience wants but you haven't covered"],
  "90_day_plan": [
    {{"week": "1-2", "action": "...", "goal": "..."}}
  ],
  "next_3_video_ideas": [
    {{"title": "...", "reason": "why this will perform well"}}
  ],
  "monetization_readiness": "not ready|approaching|ready|monetized"
}}"""

        response = await self.ai.generate(
            prompt, self.system_prompt, temperature=0.5, json_mode=True
        )
        self.track_event("channel_audited")
        return self.ai.parse_json_response(response)
