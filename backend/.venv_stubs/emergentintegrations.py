"""Minimal stub for emergentintegrations — enough to import and run without errors."""
import uuid
from typing import Any

class UserMessage:
    def __init__(self, text: str = "", role: str = "user"):
        self.text = text
        self.role = role

class LlmChat:
    def __init__(self, *, api_key: str, session_id: str, system_message: str = ""):
        self.api_key = api_key
        self.session_id = session_id
        self.system_message = system_message
        self._model = None

    def with_model(self, provider: str, model: str):
        self._model = (provider, model)
        return self

    async def send_message(self, message: UserMessage) -> str:
        # Return a generic JSON structure so downstream parsers don't crash
        return '{"kind": "text", "text": "Hello from Chitra AI (stub mode)."}'
