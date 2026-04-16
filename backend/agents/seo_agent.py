"""
MCP 2: SEO Agent v2

Improvements:
- Uses centralized prompt templates + system prompt
- CoT for keyword intent classification
- Context injection (user's existing keywords/clusters)
- Cross-module pipeline: publishes best keyword → Content agent
- Reflection on meta quality (length, keyword presence)
- Cached redirect suggestions (same broken URL → same answer)
- SERP feature targeting (featured snippet, PAA, local pack)
"""
import json
from agents.base_agent import BaseMCPAgent
from agents.prompt_templates import SYSTEM_PROMPTS, META_GENERATION_PROMPT
from database import models


class SEOAgent(BaseMCPAgent):
    MODULE_NAME = "seo"

    async def cluster_keywords(self, keywords: list[str], language: str = "en") -> dict:
        """
        Semantic keyword clustering with intent classification + content mapping.
        After clustering, publishes best primary keyword to Content agent.
        """
        kw_list = "\n".join(f"- {kw}" for kw in keywords)
        lang_label = "Hindi" if language == "hi" else "English"

        # CoT: first reason about keyword relationships, then cluster
        cot = await self.ai.think_then_answer(
            f"How should these {lang_label} keywords be grouped semantically, and what is the primary intent of each group?\n\nKeywords:\n{kw_list}",
            self.system_prompt,
        )

        prompt = f"""Based on this analysis: {cot['reasoning'][:600]}

Cluster these {lang_label} SEO keywords into semantic groups:
{kw_list}

For each cluster identify:
- The dominant search intent
- Which SERP features to target (featured snippet, PAA, local pack, etc.)
- Best content format to rank for it

Return JSON:
{{
  "clusters": [
    {{
      "cluster_name": "descriptive name",
      "intent": "informational|commercial|transactional|navigational",
      "primary_keyword": "highest volume / most important",
      "secondary_keywords": ["kw1", "kw2"],
      "serp_features": ["featured_snippet", "PAA"],
      "content_format": "listicle|how-to|comparison|landing page|FAQ",
      "content_suggestion": "specific title/angle to pursue",
      "difficulty_estimate": "low|medium|high",
      "priority_score": 1-10
    }}
  ],
  "strategy_summary": "overall keyword strategy in 2-3 sentences",
  "quick_wins": ["keyword with low difficulty and good volume"]
}}"""

        response = await self.ai.generate(
            self.inject_context(prompt), self.system_prompt,
            temperature=0.4, json_mode=True
        )
        result = self.ai.parse_json_response(response)

        # Cross-module: send best keyword to Content agent
        clusters = result.get("clusters", [])
        if clusters:
            best = max(clusters, key=lambda c: c.get("priority_score", 0))
            self.send_to_agent("content", "best_keyword", json.dumps({
                "keyword": best.get("primary_keyword"),
                "intent": best.get("intent"),
                "content_format": best.get("content_format"),
                "content_suggestion": best.get("content_suggestion"),
            }))

        self.track_event("keywords_clustered", {
            "count": len(keywords),
            "clusters": len(clusters),
            "language": language,
        })
        return result

    async def generate_meta(
        self,
        page_title: str,
        content_snippet: str,
        keyword: str,
        language: str = "en",
    ) -> dict:
        """
        Generate meta tags using the centralized template.
        Self-reflects to ensure character limits and keyword presence.
        """
        lang_instruction = (
            "Write ALL meta text in Hindi (Devanagari script)"
            if language == "hi"
            else "Write ALL meta text in English"
        )

        prompt = META_GENERATION_PROMPT.format(
            title=page_title,
            keyword=keyword,
            content_preview=content_snippet[:400],
            language_instruction=lang_instruction,
        )

        response = await self.ai.generate(
            prompt, self.system_prompt, temperature=0.4, json_mode=True, use_cache=False
        )
        result = self.ai.parse_json_response(response)

        # Validate and self-correct character limits
        meta_title = result.get("meta_title", "")
        meta_desc = result.get("meta_description", "")
        issues = []

        if len(meta_title) > 60:
            issues.append(f"meta_title too long ({len(meta_title)} chars, max 60)")
        if len(meta_desc) > 155:
            issues.append(f"meta_description too long ({len(meta_desc)} chars, max 155)")
        if keyword.lower() not in meta_title.lower():
            issues.append("keyword missing from meta_title")
        if keyword.lower() not in meta_desc.lower():
            issues.append("keyword missing from meta_description")

        if issues:
            fix_prompt = f"""Fix these SEO meta tag issues:
Issues: {', '.join(issues)}
Current meta_title: "{meta_title}"
Current meta_description: "{meta_desc}"
Keyword must appear: "{keyword}"
Language: {lang_instruction}

Return corrected JSON with same fields."""
            fixed = await self.ai.generate(
                fix_prompt, self.system_prompt, temperature=0.3, json_mode=True
            )
            fixed_result = self.ai.parse_json_response(fixed)
            result.update(fixed_result)
            result["auto_corrected"] = True
            result["corrections"] = issues

        self.track_event("meta_generated", {"language": language, "keyword": keyword})
        return result

    async def suggest_internal_links(
        self, current_page_title: str, existing_pages: list[dict]
    ) -> dict:
        """
        Suggest internal links with semantic relevance scoring.
        Uses context-injection to know user's site structure.
        """
        pages_str = "\n".join(
            f"- [{p.get('title', 'Untitled')}]({p.get('url', '#')})"
            for p in existing_pages[:25]
        )

        prompt = f"""Suggest strategic internal links for this page:

Current Page: "{current_page_title}"

Available Pages:
{pages_str}

For each suggestion consider:
- Topical relevance (same cluster or complementary)
- Link equity flow (important pages should receive more links)
- User journey (what would a reader logically want to read next?)
- Anchor text naturalness (no exact-match stuffing)

Return JSON:
{{
  "internal_links": [
    {{
      "anchor_text": "natural anchor text",
      "target_url": "...",
      "target_title": "...",
      "placement_suggestion": "where in the content to place this link",
      "relevance_score": 1-10,
      "link_type": "contextual|related|navigation"
    }}
  ],
  "linking_strategy": "overall approach for this page",
  "orphan_risk": "is this page likely orphaned? yes/no + reason"
}}"""

        response = await self.ai.generate(
            self.inject_context(prompt), self.system_prompt,
            temperature=0.5, json_mode=True
        )
        return self.ai.parse_json_response(response)

    async def generate_redirect_suggestion(
        self, broken_url: str, available_pages: list[str]
    ) -> dict:
        """
        Match broken URL to best redirect using URL semantics + fuzzy matching.
        Cached — same broken URL always returns same answer.
        """
        pages_str = "\n".join(available_pages[:40])

        prompt = f"""A page returned 404. Find the best redirect destination.

Broken URL: {broken_url}

Analysis strategy:
1. Extract intent from URL slug/path words
2. Match against available pages semantically
3. Consider URL path similarity as tie-breaker

Available pages:
{pages_str}

Return JSON:
{{
  "redirect_to": "best matching URL",
  "confidence": "high|medium|low",
  "redirect_type": "301|302",
  "reason": "why this is the best match",
  "url_similarity_score": 0-100,
  "alternative": "second best option if confidence is low"
}}"""

        response = await self.ai.generate(
            prompt, self.system_prompt,
            temperature=0.2, json_mode=True, use_cache=True
        )
        return self.ai.parse_json_response(response)

    async def audit_content_seo(self, content: str, keyword: str) -> dict:
        """
        Comprehensive SEO audit with SERP feature recommendations.
        """
        word_count = len(content.split())
        keyword_count = content.lower().count(keyword.lower())
        density = round((keyword_count / max(word_count, 1)) * 100, 2)

        prompt = f"""Perform a deep SEO audit:

Target Keyword: "{keyword}"
Actual keyword density: {density}% ({keyword_count} occurrences in {word_count} words)
Content preview: {content[:1200]}

Evaluate:
1. On-page optimization (title, headings, density)
2. Content depth & E-E-A-T signals
3. Readability (Flesch-Kincaid estimate)
4. SERP feature eligibility
5. Missing sections that competitors likely have

Return JSON:
{{
  "seo_score": 0-100,
  "keyword_density": "{density}%",
  "keyword_density_verdict": "too low|optimal|too high",
  "readability_score": 0-100,
  "readability_level": "easy|medium|difficult",
  "eeat_signals": ["present signal", "missing signal"],
  "issues": [
    {{"severity": "critical|major|minor", "issue": "...", "fix": "..."}}
  ],
  "serp_features": {{
    "featured_snippet_eligible": true/false,
    "paa_eligible": true/false,
    "how_to_schema": true/false
  }},
  "missing_sections": ["section topic 1"],
  "competitor_gap": "what top-ranking content likely has that this lacks",
  "overall_verdict": "needs major work|good foundation|publish-ready"
}}"""

        response = await self.ai.generate(
            prompt, self.system_prompt, temperature=0.3, json_mode=True
        )
        result = self.ai.parse_json_response(response)
        self.track_event("content_audited", {"keyword": keyword, "score": result.get("seo_score")})
        return result

    async def generate_topic_cluster(self, pillar_topic: str, language: str = "en") -> dict:
        """
        Build a full topic cluster (pillar + spoke pages) for a given topic.
        Publishes cluster map to Content agent.
        """
        lang_label = "Hindi" if language == "hi" else "English"

        prompt = f"""Build a complete {lang_label} topic cluster for: "{pillar_topic}"

Design a hub-and-spoke content architecture:
- 1 pillar page (broad, 3000+ words)
- 6-8 spoke pages (specific subtopics, 800-1500 words each)
- Internal linking structure

Return JSON:
{{
  "pillar": {{
    "title": "...",
    "keyword": "...",
    "word_count": 3000,
    "sections": ["section 1", "section 2"]
  }},
  "spokes": [
    {{
      "title": "...",
      "keyword": "...",
      "intent": "...",
      "word_count": 1000,
      "links_from_pillar_anchor": "anchor text"
    }}
  ],
  "content_calendar": [
    {{"week": 1, "publish": "pillar page title"}}
  ],
  "estimated_traffic_potential": "low|medium|high"
}}"""

        response = await self.ai.generate(
            prompt, self.system_prompt, temperature=0.6, max_tokens=3000, json_mode=True
        )
        result = self.ai.parse_json_response(response)

        # Share full cluster map with content agent
        self.send_to_agent("content", "topic_cluster", json.dumps(result))
        self.track_event("topic_cluster_generated", {"topic": pillar_topic})
        return result
