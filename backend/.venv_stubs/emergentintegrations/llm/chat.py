"""Minimal stub for emergentintegrations.llm.chat"""

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

    async def send_message(self, message) -> str:
        import json
        return json.dumps({"kind": "text", "text": "Hello from Chitra AI (stub mode). Please configure your API keys to enable full AI functionality."})
