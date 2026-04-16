"""
MCP 4: Social Media Agent v2

Improvements:
- Uses centralized system prompt
- Picks up blog context from Content agent (cross-module)
- Platform algorithm awareness per post type
- A/B variant generation for testing
- Trend-aware hashtag strategy (recency + niche)
- Engagement prediction scoring
- Content calendar with platform-specific timing
"""
import json
from agents.base_agent import BaseMCPAgent
from agents.prompt_templates import SYSTEM_PROMPTS
from datetime import datetime, timedelta


class SocialAgent(BaseMCPAgent):
    MODULE_NAME = "social"

    # Platform algorithm signals (2024-2025)
    PLATFORM_ALGORITHMS = {
        "instagram": "Favors Reels (3x reach), saves > likes, carousel holds attention, first 3 lines must hook",
        "twitter":   "Recency matters, replies boost reach, threads outperform single tweets, no link in first tweet",
        "linkedin":  "Dwell time > likes, personal stories outperform company posts, 3-line hook before 'see more'",
        "facebook":  "Video gets 5x organic reach, groups outperform pages, emotional content shares well",
        "youtube":   "CTR x watch time = ranking, shorts cross-promote long videos, community posts boost subscribers",
    }

    BEST_POST_TIMES = {
        "instagram": [("Tuesday", "11:00 AM"), ("Wednesday", "12:00 PM"), ("Friday", "10:00 AM")],
        "twitter":   [("Monday", "8:00 AM"),   ("Wednesday", "9:00 AM"), ("Thursday", "5:00 PM")],
        "linkedin":  [("Tuesday", "7:30 AM"),  ("Wednesday", "12:00 PM"), ("Thursday", "5:30 PM")],
        "facebook":  [("Wednesday", "1:00 PM"), ("Thursday", "9:00 AM"), ("Friday", "3:00 PM")],
    }

    async def generate_post(
        self, topic: str, platform: str, language: str = "en", post_type: str = "standard"
    ) -> dict:
        """
        Generate a platform-native post with algorithm awareness.
        Picks up blog context from Content agent automatically.
        """
        # Check if content agent published a new blog
        blog_data = self.receive_from_agent("content", "blog_published")
        blog_context = ""
        if blog_data:
            blog = json.loads(blog_data)
            blog_context = f"\nRepurpose from this blog: Title='{blog.get('title')}', Excerpt='{blog.get('excerpt', '')[:150]}'"

        algorithm = self.PLATFORM_ALGORITHMS.get(platform, "Engagement-first content")
        lang_note = "Write in Hindi" if language == "hi" else "Write in English"
        best_times = self.BEST_POST_TIMES.get(platform, [("Weekday", "10:00 AM")])

        post_type_guides = {
            "standard":    "Single post — one clear message, strong hook",
            "carousel":    "Multi-slide — each slide = one insight, slide 1 = hook, last slide = CTA",
            "thread":      "Twitter thread — 5-7 tweets, each must stand alone, numbered",
            "story":       "Ephemeral — urgent, personal, behind-the-scenes feel",
            "reel_hook":   "First 3 seconds script only — pattern interrupt, bold claim",
        }
        type_guide = post_type_guides.get(post_type, post_type_guides["standard"])

        prompt = f"""{lang_note}. Create a {platform} {post_type} post about: "{topic}"

Algorithm insight: {algorithm}
Post format guide: {type_guide}
{blog_context}

Return JSON:
{{
  "caption": "complete post text with hook + body + CTA",
  "hashtags": ["#relevant", "#niche", "#broad"],
  "hook": "first line only (most important)",
  "cta": "call to action",
  "media_suggestion": "describe ideal image/video/carousel",
  "best_post_day": "{best_times[0][0]}",
  "best_post_time": "{best_times[0][1]}",
  "algorithm_tip": "specific tip for this platform's algorithm",
  "predicted_reach": "low|medium|high",
  "engagement_prediction": {{
    "likes": "estimate",
    "comments": "estimate",
    "shares": "estimate"
  }},
  "ab_variant": "alternative hook/angle for A/B testing"
}}"""

        response = await self.ai.generate(
            self.inject_context(prompt), self.system_prompt,
            temperature=0.85, json_mode=True
        )
        result = self.ai.parse_json_response(response)
        self.track_event("post_generated", {"platform": platform, "post_type": post_type})
        return result

    async def get_trending_hashtags(self, niche: str, platform: str) -> dict:
        """
        Generate a strategic hashtag stack (not just trending — also niche + branded).
        """
        prompt = f"""Build a complete {platform} hashtag strategy for the "{niche}" niche.

Hashtag tiers:
1. Mega (1M+ posts) — max reach, low discovery chance
2. Mid (100K-1M posts) — balance of reach + discovery
3. Niche (10K-100K posts) — highly targeted, best engagement
4. Micro (<10K posts) — community, highest conversion
5. Branded — for the niche's top creators/terms

Return JSON:
{{
  "mega_tags": ["#tag"],
  "mid_tags": ["#tag"],
  "niche_tags": ["#tag"],
  "micro_tags": ["#tag"],
  "branded_tags": ["#tag"],
  "recommended_stack": ["#tag1", "#tag2", "... optimal 10-15 mix"],
  "strategy": "how to rotate these over time",
  "avoid": ["#tag — reason to avoid"],
  "platform_hashtag_limit": number
}}"""

        response = await self.ai.generate(
            prompt, self.system_prompt, temperature=0.6, json_mode=True
        )
        return self.ai.parse_json_response(response)

    async def generate_content_calendar(
        self, niche: str, platforms: list[str], days: int = 7
    ) -> dict:
        """
        Generate a multi-platform content calendar with varied formats.
        Aware of optimal posting frequency per platform.
        """
        platform_frequencies = {
            "instagram": "1/day (feed) + 3-5 stories/day",
            "twitter":   "3-5 tweets/day",
            "linkedin":  "1/day max (quality over quantity)",
            "facebook":  "1-2/day",
            "youtube":   "2-3 videos/week + 1 Short/day",
        }

        freq_notes = "\n".join(
            f"- {p}: {platform_frequencies.get(p, '1/day')}" for p in platforms
        )
        platforms_str = ", ".join(platforms)

        prompt = f"""Create a {days}-day content calendar for: "{niche}"
Platforms: {platforms_str}

Optimal posting frequency:
{freq_notes}

Rules:
- Vary content types (educational, entertaining, promotional = 4:4:2 ratio)
- Cross-post strategically (same topic, different format per platform)
- Include content pillars: tips, stories, behind-scenes, product/service, UGC ask
- Monday = motivational, Friday = fun/trending, weekend = light engagement

Return JSON:
{{
  "strategy_overview": "...",
  "content_pillars": ["pillar 1", "pillar 2"],
  "calendar": [
    {{
      "day": 1,
      "date_label": "Monday",
      "theme": "motivational",
      "posts": [
        {{
          "platform": "...",
          "content_type": "reel|carousel|post|story|thread|short",
          "topic": "...",
          "hook": "opening line",
          "hashtags": ["#tag"],
          "post_time": "HH:MM AM/PM",
          "repurpose_from": "day X post" or null
        }}
      ]
    }}
  ],
  "weekly_kpi_targets": {{
    "reach_goal": "...",
    "engagement_goal": "...",
    "follower_growth": "..."
  }}
}}"""

        response = await self.ai.generate(
            self.inject_context(prompt), self.system_prompt,
            temperature=0.75, max_tokens=4096, json_mode=True
        )
        result = self.ai.parse_json_response(response)
        self.track_event("calendar_generated", {"niche": niche, "days": days, "platforms": len(platforms)})
        return result

    async def analyze_post_performance(self, caption: str, metrics: dict) -> dict:
        """
        Deep performance analysis with algorithm attribution.
        """
        prompt = f"""Analyze this social media post performance:

Caption (first 300 chars): {caption[:300]}

Metrics:
- Likes: {metrics.get('likes', 0)}
- Comments: {metrics.get('comments', 0)}
- Shares: {metrics.get('shares', 0)}
- Saves: {metrics.get('saves', 0)}
- Reach: {metrics.get('reach', 0)}
- Impressions: {metrics.get('impressions', 0)}
- Profile visits: {metrics.get('profile_visits', 0)}

Return JSON:
{{
  "engagement_rate": "calculated %",
  "save_rate": "saves/reach %",
  "performance_rating": "poor|below average|average|good|viral",
  "algorithm_signals": {{
    "strong": ["what the algorithm liked"],
    "weak": ["what hurt reach"]
  }},
  "content_analysis": {{
    "hook_strength": "weak|moderate|strong",
    "cta_effectiveness": "...",
    "hashtag_performance": "..."
  }},
  "what_worked": ["specific element that drove engagement"],
  "what_to_improve": ["specific change for next post"],
  "next_post_recommendation": "based on what performed well",
  "boost_worthy": true/false
}}"""

        response = await self.ai.generate(
            prompt, self.system_prompt, temperature=0.4, json_mode=True
        )
        return self.ai.parse_json_response(response)

    async def repurpose_content(self, source_content: str, source_type: str, target_platforms: list[str]) -> dict:
        """
        Repurpose one piece of content into multiple platform-native formats.
        """
        platforms_str = ", ".join(target_platforms)
        prompt = f"""Repurpose this {source_type} into platform-native content for: {platforms_str}

Source content:
{source_content[:2000]}

For EACH platform, create the ideal format. Don't just copy-paste — truly adapt.

Return JSON:
{{
  "repurposed": [
    {{
      "platform": "...",
      "format": "post|thread|reel script|carousel text|story sequence",
      "content": "adapted content",
      "hashtags": ["#tag"],
      "notes": "what was changed and why"
    }}
  ]
}}"""

        response = await self.ai.generate(
            prompt, self.system_prompt, temperature=0.85, max_tokens=3000, json_mode=True
        )
        result = self.ai.parse_json_response(response)
        self.track_event("content_repurposed", {"source": source_type, "targets": len(target_platforms)})
        return result

    def get_optimal_schedule(self, platform: str, count: int = 3) -> list[dict]:
        """Return optimal posting schedule slots for a platform."""
        times = self.BEST_POST_TIMES.get(platform, [("Weekday", "10:00 AM")])
        schedule = []
        for i in range(count):
            day_offset = i + 1
            day_label, time_str = times[i % len(times)]
            date = datetime.utcnow() + timedelta(days=day_offset)
            schedule.append({
                "date": date.strftime("%Y-%m-%d"),
                "day": day_label,
                "time": time_str,
                "platform": platform,
                "slot_index": i + 1,
            })
        return schedule
