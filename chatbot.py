"""
chatbot.py — CampusMind AI core (Groq-powered).
Features: multi-turn chat, persistent memory, PDF context, Whisper voice transcription.
"""

import os, json, re, logging, tempfile
from datetime import datetime
from typing import Optional
from groq import Groq, APIError, APIConnectionError, RateLimitError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_MODEL      = "llama-3.3-70b-versatile"
DEFAULT_MAX_TOKENS = 1024
MAX_HISTORY_TURNS  = 20
MEMORY_FILE        = "campusmind_memory.json"

AVAILABLE_MODELS = {
    "llama-3.3-70b-versatile": "LLaMA 3.3 70B — Best quality",
    "llama-3.1-8b-instant":    "LLaMA 3.1 8B  — Fastest",
    "mixtral-8x7b-32768":      "Mixtral 8x7B  — Long context",
}

BASE_SYSTEM_PROMPT = """You are CampusMind AI, a friendly and knowledgeable campus assistant.
You help students with academic questions, study tips, campus life, and general knowledge.
You are warm, encouraging, and clear in your explanations.
Always remember and use personal details the user shares (name, major, interests, university).
Keep responses concise unless the user asks for more detail."""


# ══════════════════════════════════════════════════════════════
# PERSISTENT MEMORY
# ══════════════════════════════════════════════════════════════
class Memory:
    """Stores key user facts in a local JSON file across sessions."""

    def __init__(self, filepath: str = MEMORY_FILE):
        self.filepath = filepath
        self.facts: dict = {}
        self.load()

    def load(self):
        try:
            with open(self.filepath) as f:
                self.facts = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.facts = {}

    def save(self):
        with open(self.filepath, "w") as f:
            json.dump(self.facts, f, indent=2)

    def update_from_message(self, text: str):
        """Auto-extract facts like name, major, university from user messages."""
        changed = False

        # Name
        for pattern in [
            r"(?:my name is|i'm|i am|call me)\s+([A-Z][a-z]+(?: [A-Z][a-z]+)?)",
        ]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                self.facts["name"] = m.group(1).strip().title()
                changed = True
                break

        # Major / subject
        m = re.search(
            r"(?:studying|majoring in|i study|my major is|my field is)\s+([a-zA-Z &]+?)(?:\.|,|\n|$)",
            text, re.IGNORECASE
        )
        if m:
            self.facts["major"] = m.group(1).strip().title()
            changed = True

        # Year
        m = re.search(
            r"\b(freshman|sophomore|junior|senior|1st year|2nd year|3rd year|4th year|first.year|second.year|third.year|fourth.year)\b",
            text, re.IGNORECASE
        )
        if m:
            self.facts["year"] = m.group(1).lower()
            changed = True

        # University
        m = re.search(
            r"(?:at|attend|go to|from|study at)\s+([A-Z][a-zA-Z ]+?(?:University|College|Institute|School|Academy))",
            text
        )
        if m:
            self.facts["university"] = m.group(1).strip()
            changed = True

        if changed:
            self.save()

    def to_prompt_block(self) -> str:
        if not self.facts:
            return ""
        labels = {"name": "Name", "major": "Major", "year": "Year", "university": "University"}
        lines = ["Known facts about this user:"]
        for key, label in labels.items():
            if key in self.facts:
                lines.append(f"  - {label}: {self.facts[key]}")
        for k, v in self.facts.items():
            if k not in labels:
                lines.append(f"  - {k.title()}: {v}")
        return "\n".join(lines)

    def set(self, key: str, value: str):
        self.facts[key] = value
        self.save()

    def clear(self):
        self.facts = {}
        try: os.remove(self.filepath)
        except FileNotFoundError: pass

    def get_all(self) -> dict:
        return dict(self.facts)


# ══════════════════════════════════════════════════════════════
# CONVERSATION HISTORY
# ══════════════════════════════════════════════════════════════
class ConversationHistory:
    def __init__(self, max_turns: int = MAX_HISTORY_TURNS):
        self.messages: list[dict] = []
        self.max_turns = max_turns

    def add_user(self, text: str):
        self.messages.append({"role": "user", "content": text})
        self._trim()

    def add_assistant(self, text: str):
        self.messages.append({"role": "assistant", "content": text})

    def _trim(self):
        limit = self.max_turns * 2
        if len(self.messages) > limit:
            self.messages = self.messages[-limit:]

    def clear(self):
        self.messages.clear()

    def __len__(self):
        return len(self.messages)


# ══════════════════════════════════════════════════════════════
# CHATBOT
# ══════════════════════════════════════════════════════════════
class Chatbot:
    def __init__(self, api_key: Optional[str] = None,
                 model: str = DEFAULT_MODEL, max_tokens: int = DEFAULT_MAX_TOKENS):
        key = api_key or os.environ.get("GROQ_API_KEY")
        if not key:
            raise ValueError("No API key. Set GROQ_API_KEY env var or pass api_key=.")
        self.client      = Groq(api_key=key)
        self.model       = model
        self.max_tokens  = max_tokens
        self.history     = ConversationHistory()
        self.memory      = Memory()
        self.pdf_context = ""
        logger.info("CampusMind AI ready — model: %s", self.model)

    # ── System prompt builder ──────────────────────────────────
    def _system_prompt(self) -> str:
        parts = [BASE_SYSTEM_PROMPT]
        mem = self.memory.to_prompt_block()
        if mem:
            parts.append("\n" + mem)
        if self.pdf_context:
            parts.append(
                "\nThe user uploaded a document. Use it to answer questions about its academic content only.\n"
                "IMPORTANT PRIVACY RULES for this document:\n"
                "- NEVER mention, reveal, or repeat any person's name found in the document (teachers, professors, authors, instructors, students, or anyone else).\n"
                "- NEVER reveal emails, phone numbers, office hours, room numbers, or any personal contact details.\n"
                "- NEVER refer to who wrote or created the document.\n"
                "- Focus ONLY on the academic subject matter, concepts, topics, and educational content.\n"
                "--- DOCUMENT ---\n"
                + self.pdf_context[:6000] +
                "\n--- END ---"
            )
        return "\n".join(parts)

    # ── Text chat ──────────────────────────────────────────────
    def chat(self, user_message: str) -> str:
        user_message = user_message.strip()
        if not user_message:
            return "Please enter a message."
        self.memory.update_from_message(user_message)
        self.history.add_user(user_message)
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    *self.history.messages,
                ],
            )
            reply = resp.choices[0].message.content
            self.history.add_assistant(reply)
            return reply
        except RateLimitError:
            self.history.messages.pop()
            return "⚠️ Rate limit reached — wait a moment and try again."
        except APIConnectionError:
            self.history.messages.pop()
            return "⚠️ Connection error — check your internet."
        except APIError as e:
            self.history.messages.pop()
            return f"⚠️ API error: {e.message}"

    # ── Voice transcription (Groq Whisper — same API key) ─────
    def transcribe_audio(self, audio_bytes: bytes) -> str:
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            with open(tmp_path, "rb") as f:
                result = self.client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=("audio.wav", f, "audio/wav"),
                )
            os.unlink(tmp_path)
            return result.text.strip()
        except Exception as e:
            logger.error("Transcription failed: %s", e)
            return ""

    # ── PDF context ────────────────────────────────────────────
    def set_pdf_context(self, text: str):
        self.pdf_context = text

    def clear_pdf_context(self):
        self.pdf_context = ""

    # ── Misc ───────────────────────────────────────────────────
    def reset(self):
        self.history.clear()

    def change_model(self, model: str):
        self.model = model

    @property
    def turn_count(self) -> int:
        return len(self.history) // 2
