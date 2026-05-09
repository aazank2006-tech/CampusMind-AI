"""
chatbot.py — CampusMind AI core (Groq-powered).
Handles conversation history, API calls, and error recovery.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional

from groq import Groq, APIError, APIConnectionError, RateLimitError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_SYSTEM_PROMPT = """You are a helpful, friendly, and knowledgeable assistant.
You provide clear, concise answers and ask follow-up questions when needed.
You are honest about uncertainty and admit when you don't know something.
Keep responses conversational and appropriately brief unless detail is requested."""

DEFAULT_MODEL      = "llama-3.3-70b-versatile"
DEFAULT_MAX_TOKENS = 1024
MAX_HISTORY_TURNS  = 20

AVAILABLE_MODELS = {
    "llama-3.3-70b-versatile": "LLaMA 3.3 70B — Best quality",
    "llama-3.1-8b-instant":    "LLaMA 3.1 8B  — Fastest",
    "mixtral-8x7b-32768":      "Mixtral 8x7B  — Long context",
}


# ── Conversation history ───────────────────────────────────────────────────────
class ConversationHistory:
    def __init__(self, max_turns: int = MAX_HISTORY_TURNS):
        self.messages: list[dict] = []
        self.max_turns = max_turns

    def add_user(self, text: str) -> None:
        self.messages.append({"role": "user", "content": text})
        self._trim()

    def add_assistant(self, text: str) -> None:
        self.messages.append({"role": "assistant", "content": text})

    def _trim(self) -> None:
        max_messages = self.max_turns * 2
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]

    def clear(self) -> None:
        self.messages.clear()

    def to_list(self) -> list[dict]:
        return list(self.messages)

    def save(self, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"saved_at": datetime.utcnow().isoformat(),
                       "messages": self.messages}, f, indent=2)

    def load(self, filepath: str) -> None:
        with open(filepath, encoding="utf-8") as f:
            self.messages = json.load(f).get("messages", [])

    def __len__(self) -> int:
        return len(self.messages)


# ── Chatbot ────────────────────────────────────────────────────────────────────
class Chatbot:
    def __init__(
        self,
        api_key: Optional[str] = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ):
        key = api_key or os.environ.get("GROQ_API_KEY")
        if not key:
            raise ValueError("No API key. Set GROQ_API_KEY env var or pass api_key=")

        self.client        = Groq(api_key=key)
        self.system_prompt = system_prompt
        self.model         = model
        self.max_tokens    = max_tokens
        self.history       = ConversationHistory()
        logger.info("Chatbot ready — model: %s", self.model)

    def chat(self, user_message: str) -> str:
        user_message = user_message.strip()
        if not user_message:
            return "Please enter a message."

        self.history.add_user(user_message)
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    *self.history.messages,
                ],
            )
            reply = resp.choices[0].message.content
            self.history.add_assistant(reply)
            return reply

        except RateLimitError:
            self.history.messages.pop()
            return "⚠️ Rate limit reached — please wait a moment and try again."
        except APIConnectionError:
            self.history.messages.pop()
            return "⚠️ Connection error — check your internet connection."
        except APIError as e:
            self.history.messages.pop()
            return f"⚠️ API error: {e.message}"

    def reset(self) -> None:
        self.history.clear()

    def save_conversation(self, path: str = "conversation.json") -> None:
        self.history.save(path)

    def load_conversation(self, path: str = "conversation.json") -> None:
        self.history.load(path)

    def change_model(self, model: str) -> None:
        self.model = model
        logger.info("Model switched to: %s", model)

    def change_system_prompt(self, prompt: str) -> None:
        self.system_prompt = prompt

    @property
    def turn_count(self) -> int:
        return len(self.history) // 2
