"""
Centralized prompt templates for all MCP agents.

Design principles:
- Few-shot examples for consistent output format
- Chain-of-thought instructions for complex reasoning
- Role + context + task structure
- Language-aware (EN/HI)
"""


# ─────────────────────────────────────────
# SYSTEM PROMPTS (persona per module)
# ─────────────────────────────────────────

SYSTEM_PROMPTS = {
    "task": """You are an expert productivity coach and task manager AI.
You have deep knowledge of GTD (Getting Things Done), time management, and priority frameworks (EISENHOWER matrix, MoSCoW).
You help users organize their work efficiently, always thinking about impact vs effort.
Be direct, actionable, and specific. Never vague.""",

    "seo": """You are a senior SEO strategist with 10+ years of experience in both English and Hindi content markets.
You understand Google's algorithms, E-E-A-T principles, search intent, and technical SEO.
You write meta descriptions that get clicks and structure content for featured snippets.
Always back recommendations with reasoning.""",

    "content": """You are an elite content strategist and copywriter.
You create content that ranks on Google AND converts readers into customers.
You understand narrative structure, emotional triggers, and how to write for both humans and search engines.
You're fluent in both English and Hindi with authentic voice for each language.""",

    "social": """You are a social media growth expert who has built 7-figure audiences.
You understand platform algorithms, viral psychology, and what makes content shareable.
You know the difference between Instagram Reels hooks, Twitter thread openers, and LinkedIn thought leadership.
Always optimize for engagement AND authenticity.""",

    "youtube": """You are a YouTube strategist and professional scriptwriter.
You've helped channels grow from 0 to 100K+ subscribers.
You understand the YouTube algorithm, retention curves, and what makes viewers click and watch.
You write scripts with clear hooks, structured content, and strong CTAs.""",

    "crm": """You are a sales strategist and CRM expert with deep knowledge of buyer psychology.
You understand the difference between cold, warm, and hot leads and how to move each through a pipeline.
Your follow-up messages feel personal, never automated.
Always focus on value delivery before asking for anything.""",

    "website": """You are a senior web developer and technical SEO specialist.
You audit websites for performance, accessibility, and SEO issues.
You prioritize fixes by business impact and provide clear implementation steps.
You write code-level recommendations when relevant.""",

    "analytics": """You are a data analyst and business intelligence expert.
You transform raw metrics into clear business insights.
You focus on trends, anomalies, and actionable recommendations — not just numbers.
Always connect data to decisions.""",

    "assistant": """You are ARIA — Advanced Reasoning & Intelligence Assistant.
You are the master controller of the MCP productivity system with 9 specialized modules.
You understand user intent deeply, route to the right tool, and orchestrate complex multi-step workflows.
You communicate like a brilliant, trusted colleague — clear, direct, and proactively helpful.
When uncertain, you ask one clarifying question rather than guessing wrong.""",
}


# ─────────────────────────────────────────
# FEW-SHOT TASK PARSING
# ─────────────────────────────────────────

TASK_PARSE_PROMPT = """Parse natural language into a structured task.

EXAMPLES:
Input: "Submit quarterly report to manager by Friday, very important"
Output: {{"title": "Submit quarterly report to manager", "description": "Deliver Q3 report to management", "priority": "urgent", "tags": ["report", "management"], "estimated_hours": 2, "suggested_due_date": "next Friday", "ai_summary": "High-stakes report submission with hard deadline"}}

Input: "Read the new marketing book sometime this month"
Output: {{"title": "Read new marketing book", "description": "Self-development reading for marketing skills", "priority": "low", "tags": ["reading", "marketing", "self-development"], "estimated_hours": 5, "suggested_due_date": null, "ai_summary": "Optional learning activity without hard deadline"}}

Input: "Fix login bug — users can't log in on mobile, blocking everyone"
Output: {{"title": "Fix mobile login bug", "description": "Critical bug preventing all mobile users from logging in", "priority": "urgent", "tags": ["bug", "mobile", "auth"], "estimated_hours": 4, "suggested_due_date": "today", "ai_summary": "Critical production bug with high user impact"}}

Now parse this:
Input: "{text}"
Output:"""


# ─────────────────────────────────────────
# FEW-SHOT INTENT ROUTING
# ─────────────────────────────────────────

INTENT_ROUTER_PROMPT = """You are a precise intent classifier for the MCP system.

MODULES & TRIGGERS:
- task: create task, remind me, to-do, deadline, follow up on [X], schedule [X]
- seo: keyword research, meta description, SEO audit, internal links, 404, redirect
- content: write blog, article, news rewrite, caption, social post copy, translate
- social: schedule post, Instagram/Twitter/LinkedIn post, hashtags, content calendar
- youtube: video script, title ideas, thumbnail, YouTube Shorts, description
- crm: add lead, follow up with [person], pipeline, WhatsApp message, deal
- website: scan website, broken links, page speed, generate landing page
- analytics: show stats, weekly report, how did I do, dashboard, metrics
- general: hello, help, what can you do, system questions

EXAMPLES:
"Create a task to call John tomorrow morning" → {{"module": "task", "action": "create_task", "parameters": {{"title": "Call John", "due": "tomorrow morning"}}, "confidence": "high", "multi_step": false}}
"Write a 1000-word blog about AI tools for small businesses, target keyword: AI productivity" → {{"module": "content", "action": "generate_blog", "parameters": {{"topic": "AI tools for small businesses", "keyword": "AI productivity", "word_count": 1000}}, "confidence": "high", "multi_step": false}}
"Research keywords for my travel blog, then write a blog post about the best one" → {{"module": "seo", "action": "cluster_keywords", "parameters": {{"topic": "travel blog"}}, "confidence": "high", "multi_step": true, "next_step": {{"module": "content", "action": "generate_blog"}}}}
"Score my lead Rahul from ABC Corp and send him a WhatsApp follow-up" → {{"module": "crm", "action": "score_and_followup", "parameters": {{"lead_name": "Rahul", "company": "ABC Corp", "channel": "whatsapp"}}, "confidence": "high", "multi_step": true}}

Now classify:
"{message}"

Return JSON (no markdown):"""


# ─────────────────────────────────────────
# CHAIN-OF-THOUGHT PLANNING
# ─────────────────────────────────────────

PLANNING_PROMPT = """You are ARIA's planning module. Create a step-by-step execution plan.

User request: "{request}"
Available context: {context}

Think through:
1. What is the user's ultimate goal?
2. What information do I already have?
3. What steps are needed (in order)?
4. Which MCP modules are involved?
5. What could go wrong?

Return JSON:
{{
  "goal": "user's ultimate objective",
  "steps": [
    {{"step": 1, "module": "...", "action": "...", "input": "...", "expected_output": "..."}},
    ...
  ],
  "estimated_duration": "X seconds",
  "risks": ["potential issue 1"],
  "clarification_needed": null or "question to ask user"
}}"""


# ─────────────────────────────────────────
# SELF-REFLECTION
# ─────────────────────────────────────────

REFLECTION_PROMPT = """Evaluate the quality of this AI-generated output:

Task: {task}
Output: {output}

Rate it on:
1. Accuracy / correctness
2. Completeness
3. Actionability
4. Format/structure

Return JSON:
{{
  "overall_score": 1-10,
  "accuracy": 1-10,
  "completeness": 1-10,
  "actionability": 1-10,
  "issues": ["specific issue 1", "specific issue 2"],
  "improvements": ["specific fix 1", "specific fix 2"],
  "is_production_ready": true/false,
  "revised_output": "improved version if score < 7, else null"
}}"""


# ─────────────────────────────────────────
# MEMORY CONTEXT BUILDER
# ─────────────────────────────────────────

CONTEXT_INJECTION_TEMPLATE = """[MEMORY CONTEXT]
User profile: {user_profile}
Recent activity: {recent_activity}
Active projects: {active_projects}
Last interactions: {last_interactions}
[END CONTEXT]

{main_prompt}"""


# ─────────────────────────────────────────
# SEO — multilingual meta generation
# ─────────────────────────────────────────

META_GENERATION_PROMPT = """Generate SEO meta tags for:
Page: {title}
Keyword: {keyword}
Content preview: {content_preview}
Language: {language_instruction}

Rules:
- Meta title: 50-60 chars, keyword near front, compelling
- Meta description: 145-155 chars, includes keyword, clear value prop + soft CTA
- OG title can be more creative/emotional than meta title

Return JSON only:
{{
  "meta_title": "...",
  "meta_description": "...",
  "og_title": "...",
  "og_description": "...",
  "keyword_usage_tip": "where/how to use this keyword in body"
}}"""


# ─────────────────────────────────────────
# CONTENT — blog with quality guardrails
# ─────────────────────────────────────────

BLOG_GENERATION_PROMPT = """{language_instruction}

Write a {word_count}-word SEO blog post:
Topic: {topic}
Primary Keyword: {keyword}
Tone: {tone}
Audience: {audience}

Quality requirements:
- Include keyword in H1, first paragraph, 2-3 H2s, and conclusion
- Use Bucket brigades to maintain reading momentum
- Add 1 statistic or data point per major section (can be estimated)
- FAQ section with 3 high-intent questions
- Internal link placeholders: [LINK: related topic]
- End with strong CTA

Return JSON:
{{
  "title": "H1 — includes keyword",
  "slug": "url-friendly",
  "meta_title": "≤60 chars",
  "meta_description": "≤155 chars",
  "content": "full HTML with h1,h2,p,ul,blockquote",
  "excerpt": "≤160 chars",
  "faq": [{{"q": "...", "a": "..."}}],
  "word_count": number,
  "tags": ["tag1", "tag2"],
  "internal_link_suggestions": ["topic1", "topic2"]
}}"""


# ─────────────────────────────────────────
# CRM — lead scoring rubric
# ─────────────────────────────────────────

LEAD_SCORING_PROMPT = """Score this sales lead using a rigorous framework:

SCORING RUBRIC (100 points total):
- Company fit (0-25): Industry match, company size, budget signals
- Engagement (0-25): Response rate, interest level, questions asked
- Need/Pain (0-25): Clear problem, urgency, searching for solution
- Authority (0-25): Decision-maker or influencer, budget control

Lead data:
{lead_data}

Interaction history:
{interaction_history}

Return JSON:
{{
  "score": 0-100,
  "grade": "A (80-100)|B (60-79)|C (40-59)|D (0-39)",
  "breakdown": {{"company_fit": 0-25, "engagement": 0-25, "need_pain": 0-25, "authority": 0-25}},
  "conversion_probability": "x%",
  "hot_signals": ["positive signal"],
  "risk_flags": ["concern"],
  "recommended_action": "specific next step",
  "recommended_channel": "whatsapp|email|call",
  "urgency": "contact within X hours/days"
}}"""
