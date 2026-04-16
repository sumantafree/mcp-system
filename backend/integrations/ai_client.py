"""
Unified AI Client — production-grade.

Improvements over v1:
- True async execution via asyncio.to_thread (Gemini) + async OpenAI
- Automatic retry with exponential backoff
- Provider fallback: Gemini → OpenAI on failure
- Response streaming (async generator)
- Prompt caching (TTL-based, avoids redundant API calls)
- Multi-turn conversation support
- Token usage tracking
- Rate limit detection + wait
"""
import asyncio
import hashlib
import json
import logging
import time
from typing import AsyncGenerator, Optional

import google.generativeai as genai
from openai import AsyncOpenAI

from core.config import settings

logger = logging.getLogger("mcp.ai")

# ── Configure providers ────────────────────────────────────────────────────
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

openai_async = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None


# ── Simple TTL cache ───────────────────────────────────────────────────────
class _PromptCache:
    """In-process TTL cache for identical prompt+provider combos."""

    def __init__(self, ttl_seconds: int = 300):
        self._store: dict[str, tuple[str, float]] = {}
        self.ttl = ttl_seconds

    def _key(self, provider: str, prompt: str, system: str) -> str:
        raw = f"{provider}:{system}:{prompt}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, provider: str, prompt: str, system: str) -> Optional[str]:
        k = self._key(provider, prompt, system)
        entry = self._store.get(k)
        if entry and (time.time() - entry[1]) < self.ttl:
            return entry[0]
        return None

    def set(self, provider: str, prompt: str, system: str, value: str):
        k = self._key(provider, prompt, system)
        self._store[k] = (value, time.time())

    def invalidate_expired(self):
        now = time.time()
        self._store = {k: v for k, v in self._store.items() if now - v[1] < self.ttl}


_cache = _PromptCache(ttl_seconds=300)


# ── Main Client ────────────────────────────────────────────────────────────
class AIClient:
    """
    Single interface for Gemini + OpenAI.
    All agents use this class exclusively.
    """

    RETRY_DELAYS = [1, 2, 4]  # seconds between retries

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or settings.DEFAULT_AI_PROVIDER

    # ── Public API ──────────────────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        json_mode: bool = False,
        use_cache: bool = False,
        conversation: Optional[list[dict]] = None,
    ) -> str:
        """
        Generate text. Retries on failure and falls back to secondary provider.

        Args:
            prompt: User message.
            system_prompt: System/persona instruction.
            temperature: Creativity (0 = deterministic, 1 = creative).
            max_tokens: Max output tokens.
            json_mode: Force JSON-only output.
            use_cache: Cache identical prompts for 5 minutes.
            conversation: Optional prior turns [{role, content}, ...] for multi-turn.
        """
        if json_mode:
            prompt = prompt + "\n\nRespond ONLY with valid JSON. No markdown, no explanation."

        # Cache check (skip for creative / non-deterministic calls)
        if use_cache and temperature < 0.3:
            cached = _cache.get(self.provider, prompt, system_prompt or "")
            if cached:
                logger.debug("Cache hit")
                return cached

        result = await self._generate_with_retry(
            prompt, system_prompt, temperature, max_tokens, conversation
        )

        if use_cache and temperature < 0.3:
            _cache.set(self.provider, prompt, system_prompt or "", result)

        return result

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Streaming response — yields text chunks as they arrive."""
        if self.provider == "gemini":
            async for chunk in self._gemini_stream(prompt, system_prompt, temperature, max_tokens):
                yield chunk
        else:
            async for chunk in self._openai_stream(prompt, system_prompt, temperature, max_tokens):
                yield chunk

    async def think_then_answer(
        self,
        question: str,
        system_prompt: Optional[str] = None,
        context: Optional[str] = None,
    ) -> dict:
        """
        Chain-of-Thought: first reason step-by-step, then produce final answer.
        Returns {"reasoning": "...", "answer": "..."}.
        """
        cot_prompt = f"""Think step by step before answering.

{"Context:\n" + context if context else ""}

Question: {question}

First write your reasoning (prefix with THINKING:), then your final answer (prefix with ANSWER:)."""

        raw = await self.generate(cot_prompt, system_prompt, temperature=0.5, max_tokens=2048)

        reasoning, answer = "", raw
        if "THINKING:" in raw and "ANSWER:" in raw:
            parts = raw.split("ANSWER:", 1)
            reasoning = parts[0].replace("THINKING:", "").strip()
            answer = parts[1].strip()

        return {"reasoning": reasoning, "answer": answer}

    async def reflect(self, original_output: str, task_description: str) -> dict:
        """
        Self-reflection: evaluate own output quality and suggest improvements.
        Returns {"score": 1-10, "issues": [...], "improved": "..."}.
        """
        prompt = f"""Evaluate this AI output and improve it if needed:

Task: {task_description}
Output: {original_output[:1500]}

Return JSON:
{{
  "score": 1-10,
  "issues": ["issue1", "issue2"],
  "improved": "improved version if score < 8, else same as output",
  "is_acceptable": true/false
}}"""
        raw = await self.generate(prompt, temperature=0.3, json_mode=True, use_cache=False)
        return self.parse_json_response(raw)

    def parse_json_response(self, text: str) -> dict:
        """Robust JSON parser — handles markdown fences, trailing commas, partial JSON."""
        text = text.strip()
        # Strip ```json ... ``` or ``` ... ```
        if text.startswith("```"):
            lines = text.split("\n")
            # Find closing fence
            end = next((i for i in range(len(lines) - 1, 0, -1) if lines[i].strip() == "```"), len(lines))
            text = "\n".join(lines[1:end])
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON object/array from messy text
            for start_char, end_char in [('{', '}'), ('[', ']')]:
                start = text.find(start_char)
                end = text.rfind(end_char)
                if start != -1 and end != -1 and end > start:
                    try:
                        return json.loads(text[start:end + 1])
                    except json.JSONDecodeError:
                        pass
            logger.warning(f"Could not parse JSON response: {text[:200]}")
            return {"raw": text, "parse_error": True}

    def count_tokens_estimate(self, text: str) -> int:
        """Rough token estimate (~4 chars per token)."""
        return len(text) // 4

    # ── Private: retry + fallback ───────────────────────────────────────

    async def _generate_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        conversation: Optional[list[dict]],
    ) -> str:
        last_error = None
        providers = [self.provider]
        # Add fallback provider
        if self.provider == "gemini" and openai_async:
            providers.append("openai")
        elif self.provider == "openai" and settings.GEMINI_API_KEY:
            providers.append("gemini")

        for provider in providers:
            for attempt, delay in enumerate([0] + self.RETRY_DELAYS):
                if delay:
                    await asyncio.sleep(delay)
                try:
                    if provider == "gemini":
                        return await self._gemini_generate(
                            prompt, system_prompt, temperature, max_tokens, conversation
                        )
                    else:
                        return await self._openai_generate(
                            prompt, system_prompt, temperature, max_tokens, conversation
                        )
                except Exception as e:
                    last_error = e
                    err_str = str(e).lower()
                    # Rate limit — wait longer
                    if "429" in err_str or "rate" in err_str:
                        wait = delay * 3 or 10
                        logger.warning(f"Rate limit on {provider}, waiting {wait}s")
                        await asyncio.sleep(wait)
                    elif "quota" in err_str or "billing" in err_str:
                        logger.error(f"{provider} quota exceeded, switching provider")
                        break  # skip retries, try next provider
                    else:
                        logger.warning(f"{provider} attempt {attempt + 1} failed: {e}")

        raise RuntimeError(f"All AI providers failed. Last error: {last_error}")

    async def _gemini_generate(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        conversation: Optional[list[dict]],
    ) -> str:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
            system_instruction=system_prompt or "",
        )

        if conversation:
            # Multi-turn: build history
            history = []
            for msg in conversation[:-1]:
                history.append({
                    "role": "user" if msg["role"] == "user" else "model",
                    "parts": [msg["content"]],
                })
            chat = model.start_chat(history=history)
            response = await asyncio.to_thread(chat.send_message, prompt)
        else:
            response = await asyncio.to_thread(model.generate_content, prompt)

        return response.text.strip()

    async def _openai_generate(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        conversation: Optional[list[dict]],
    ) -> str:
        if not openai_async:
            raise ValueError("OpenAI API key not configured")

        messages: list[dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if conversation:
            messages.extend(conversation)
        else:
            messages.append({"role": "user", "content": prompt})

        response = await openai_async.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()

    # ── Streaming ────────────────────────────────────────────────────────

    async def _gemini_stream(
        self, prompt: str, system_prompt: Optional[str], temperature: float, max_tokens: int
    ) -> AsyncGenerator[str, None]:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=genai.types.GenerationConfig(
                temperature=temperature, max_output_tokens=max_tokens
            ),
            system_instruction=system_prompt or "",
        )
        response = await asyncio.to_thread(model.generate_content, prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text

    async def _openai_stream(
        self, prompt: str, system_prompt: Optional[str], temperature: float, max_tokens: int
    ) -> AsyncGenerator[str, None]:
        if not openai_async:
            raise ValueError("OpenAI API key not configured")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        stream = await openai_async.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


ai_client = AIClient()
