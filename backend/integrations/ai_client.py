"""
Unified AI Client — production-grade.
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

# Configure providers
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

openai_async = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None


# Cache
class _PromptCache:
    def __init__(self, ttl_seconds: int = 300):
        self._store = {}
        self.ttl = ttl_seconds

    def _key(self, provider: str, prompt: str, system: str) -> str:
        raw = f"{provider}:{system}:{prompt}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, provider: str, prompt: str, system: str):
        k = self._key(provider, prompt, system)
        entry = self._store.get(k)
        if entry and (time.time() - entry[1]) < self.ttl:
            return entry[0]
        return None

    def set(self, provider: str, prompt: str, system: str, value: str):
        k = self._key(provider, prompt, system)
        self._store[k] = (value, time.time())


_cache = _PromptCache()


class AIClient:
    RETRY_DELAYS = [1, 2, 4]

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or settings.DEFAULT_AI_PROVIDER

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

        if json_mode:
            prompt += "\n\nRespond ONLY with valid JSON."

        if use_cache and temperature < 0.3:
            cached = _cache.get(self.provider, prompt, system_prompt or "")
            if cached:
                return cached

        result = await self._generate_with_retry(
            prompt, system_prompt, temperature, max_tokens, conversation
        )

        if use_cache and temperature < 0.3:
            _cache.set(self.provider, prompt, system_prompt or "", result)

        return result

    async def think_then_answer(
        self,
        question: str,
        system_prompt: Optional[str] = None,
        context: Optional[str] = None,
    ) -> dict:

        # ✅ FIXED PART (no backslash inside f-string expression)
        context_text = f"Context:\n{context}" if context else ""

        cot_prompt = f"""Think step by step before answering.

{context_text}

Question: {question}

First write your reasoning (prefix with THINKING:), then your final answer (prefix with ANSWER:)."""

        raw = await self.generate(cot_prompt, system_prompt, temperature=0.5)

        reasoning, answer = "", raw
        if "THINKING:" in raw and "ANSWER:" in raw:
            parts = raw.split("ANSWER:", 1)
            reasoning = parts[0].replace("THINKING:", "").strip()
            answer = parts[1].strip()

        return {"reasoning": reasoning, "answer": answer}

    def parse_json_response(self, text: str) -> dict:
        text = text.strip()
        try:
            return json.loads(text)
        except:
            return {"raw": text}

    async def _generate_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        conversation: Optional[list[dict]],
    ) -> str:

        providers = [self.provider]

        if self.provider == "gemini" and openai_async:
            providers.append("openai")

        for provider in providers:
            for delay in [0] + self.RETRY_DELAYS:
                if delay:
                    await asyncio.sleep(delay)
                try:
                    if provider == "gemini":
                        return await self._gemini_generate(prompt)
                    else:
                        return await self._openai_generate(prompt)
                except Exception:
                    continue

        raise RuntimeError("All providers failed")

    async def _gemini_generate(self, prompt: str) -> str:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text.strip()

    async def _openai_generate(self, prompt: str) -> str:
        if not openai_async:
            raise ValueError("OpenAI not configured")

        response = await openai_async.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()


ai_client = AIClient()