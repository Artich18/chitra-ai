"""
AI Orchestrator
---------------
Modular provider layer. Production rules:
- Primary: Gemini 2.5 Flash
- Fallback: OpenAI GPT-5.5
- Smart routing per capability
- Automatic fallback on provider failure (logged)
- Adding Claude/Grok/DeepSeek = drop in a new Provider class

Uses the `emergentintegrations` library so we can pass any provider key.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from typing import Any

from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)


# ---------- Capability routing ----------
# Tasks where Gemini wins (analytical, structured, fast)
GEMINI_TASKS = {
    "job_search",
    "resume_analysis",
    "ats_score",
    "skill_gap",
    "career_roadmap",
    "career_guidance",
    "explain_jd",
    "missing_skills",
    "salary_insights",
    "company_research",
    "learning_resources",
}

# Tasks where OpenAI wins (long-form writing, persona)
OPENAI_TASKS = {
    "resume_rewrite",
    "cover_letter",
    "hr_communication",
    "mock_interview",
    "interview_simulation",
}


class BaseProvider:
    name = "base"

    async def complete(self, system: str, prompt: str, *, json_mode: bool = False) -> str:
        raise NotImplementedError


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model

    async def complete(self, system: str, prompt: str, *, json_mode: bool = False) -> str:
        if json_mode:
            system = system + "\n\nIMPORTANT: Reply with ONLY a JSON object. No markdown, no code fences, no extra text."
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"chitra-{uuid.uuid4()}",
            system_message=system,
        ).with_model("gemini", self.model)
        return await chat.send_message(UserMessage(text=prompt))


class OpenAIProvider(BaseProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-5.5"):
        self.api_key = api_key
        self.model = model

    async def complete(self, system: str, prompt: str, *, json_mode: bool = False) -> str:
        if json_mode:
            system = system + "\n\nIMPORTANT: Reply with ONLY a JSON object. No markdown, no code fences, no extra text."
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"chitra-{uuid.uuid4()}",
            system_message=system,
        ).with_model("openai", self.model)
        return await chat.send_message(UserMessage(text=prompt))


class AIOrchestrator:
    """Routes requests to the right provider and falls back gracefully."""

    def __init__(self):
        self.gemini = GeminiProvider(
            api_key=os.environ.get("GEMINI_API_KEY", ""),
            model=os.environ.get("PRIMARY_MODEL", "gemini-2.5-flash"),
        )
        self.openai = OpenAIProvider(
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            model=os.environ.get("FALLBACK_MODEL", "gpt-5.5"),
        )
        # Emergent-managed key as a last-resort fallback so the product
        # keeps working even when user-supplied quotas are exhausted.
        emergent_key = os.environ.get("EMERGENT_LLM_KEY", "")
        self.emergent = GeminiProvider(
            api_key=emergent_key,
            model="gemini-2.5-flash",
        ) if emergent_key else None
        # Registry — future providers (Claude, Grok, DeepSeek) plug in here
        self._providers: dict[str, BaseProvider] = {
            "gemini": self.gemini,
            "openai": self.openai,
        }
        if self.emergent:
            self._providers["emergent"] = self.emergent

    def register_provider(self, name: str, provider: BaseProvider) -> None:
        """Public hook for Claude/Grok/DeepSeek/OpenRouter integrations."""
        self._providers[name] = provider

    def _pick_primary(self, task: str, preferred: str | None) -> list[BaseProvider]:
        """Return ordered provider chain: primary → fallback → emergency."""
        if preferred and preferred in self._providers and preferred != "auto":
            primary = self._providers[preferred]
            others = [p for p in (self.gemini, self.openai) if p is not primary]
            chain = [primary, *others]
        elif task in OPENAI_TASKS:
            chain = [self.openai, self.gemini]
        else:
            chain = [self.gemini, self.openai]
        if self.emergent and self.emergent not in chain:
            chain.append(self.emergent)
        return chain

    async def generate(
        self,
        *,
        system: str,
        prompt: str,
        task: str = "career_guidance",
        json_mode: bool = False,
        preferred_provider: str | None = None,
    ) -> dict[str, Any]:
        """Run the request through the orchestrator. Returns:
           { 'text': str, 'provider': 'gemini'|'openai'|'emergent', 'task': task }
        """
        for provider in self._pick_primary(task, preferred_provider):
            try:
                text = await provider.complete(system, prompt, json_mode=json_mode)
                return {"text": text, "provider": provider.name, "task": task}
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    "[AIOrchestrator] %s failed for task=%s err=%s — falling back",
                    provider.name, task, str(e)[:200],
                )
                continue

        raise RuntimeError("All AI providers failed")

    async def generate_json(
        self,
        *,
        system: str,
        prompt: str,
        task: str = "career_guidance",
        preferred_provider: str | None = None,
    ) -> dict[str, Any]:
        """Generate + parse JSON. Tries every provider in the chain before failing."""
        last_err: Exception | None = None
        for provider in self._pick_primary(task, preferred_provider):
            try:
                text = await provider.complete(system, prompt, json_mode=True)
                parsed = _safe_json(text)
                return {"data": parsed, "provider": provider.name, "task": task}
            except JsonParseError as e:
                logger.warning("[AIOrchestrator] %s returned unparseable JSON for task=%s — falling back", provider.name, task)
                last_err = e
                continue
            except Exception as e:  # noqa: BLE001
                logger.warning("[AIOrchestrator] %s failed (json) task=%s err=%s — falling back", provider.name, task, str(e)[:200])
                last_err = e
                continue
        raise RuntimeError(f"All AI providers failed to return valid JSON: {last_err}")


class JsonParseError(Exception):
    """Raised when AI output cannot be coerced into JSON."""


def _safe_json(text: str) -> Any:
    """Parse a JSON object that may be wrapped in code fences or prose.

    Raises JsonParseError on hard failure — never returns raw model text
    (so it can't leak into the user-facing chat surface).
    """
    if not text:
        raise JsonParseError("empty response")
    cleaned = text.strip()

    # 1) Strip ``` ```json ... ``` fences (anywhere)
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if fence:
        try:
            return json.loads(fence.group(1))
        except Exception:
            pass

    # 2) Direct parse
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # 3) Walk the string, find the FIRST '{' and balance braces to extract
    #    the first complete JSON object — ignores leading prose and trailing junk.
    start = cleaned.find("{")
    while start != -1:
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(cleaned)):
            ch = cleaned[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = cleaned[start:i + 1]
                    try:
                        return json.loads(candidate)
                    except Exception:
                        break
        # next candidate
        start = cleaned.find("{", start + 1)

    raise JsonParseError(f"could not parse JSON from model output (len={len(text)})")


# Lazy singleton
_orchestrator: AIOrchestrator | None = None


def get_orchestrator() -> AIOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AIOrchestrator()
    return _orchestrator
