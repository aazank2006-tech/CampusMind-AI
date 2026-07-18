# 🎓 CampusMind AI

A campus-focused conversational assistant built with **Streamlit** and the **Groq API**. CampusMind AI chats in multiple personas, remembers facts about you across a session, answers questions about uploaded PDFs, and ships with a custom dark-themed UI.

---

## ✨ Features

- **Fast multi-turn chat** powered by Groq-hosted LLMs, with conversation history trimmed automatically to stay within context limits.
- **Switchable personas** — Campus Assistant, Python Tutor, Writing Coach, Study Planner, and Research Helper each carry their own system prompt, scoped per session (not shared between users).
- **Persistent memory** — auto-detects and remembers your name, major, year, and university from what you type, and injects them into future responses.
- **PDF-aware Q&A** — upload a document and ask questions about it. Built-in privacy rules stop the model from surfacing names, emails, or contact details found in the file.
- **Model picker** — swap between `llama-3.3-70b-versatile` (best quality), `llama-3.1-8b-instant` (fastest), and `mixtral-8x7b-32768` (long context) on the fly.
- **Voice-ready backend** — Groq Whisper transcription and gTTS speech synthesis are implemented in `chatbot.py`, ready to wire into a UI voice mode.
- **Chat export** — download the full conversation as JSON.
- **Custom UI** — dark theme, Syne/DM Mono typography, animated collapsible sidebar, auto-scrolling chat.

---

## 📁 Project Structure

```
campusmind-ai/
├── app.py                # Streamlit interface
├── chatbot.py             # Core chatbot logic (Groq client, memory, personas, PDF context)
├── firestore_store.py      # Firestore persistence layer (memory + chat history)
├── requirements.txt        # Python dependencies
├── .streamlit/
│   └── secrets.toml           # Local secrets template (not committed)
└── README.md
```

---

## 🛠 Requirements

- Python 3.9+
- A [Groq API key](https://console.groq.com/keys) (free tier available)

`requirements.txt`:

```
streamlit>=1.35
groq>=0.9
pdfplumber>=0.11
gTTS>=2.5
firebase-admin>=6.5
```

---

## 🚀 Setup

**1. Clone and enter the project**
```bash
git clone https://github.com/<your-username>/campusmind-ai.git
cd campusmind-ai
```

**2. Create a virtual environment and install dependencies**
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Set your Groq API key**

Locally, export it as an environment variable:
```bash
export GROQ_API_KEY=gsk_your_key_here      # Windows: set GROQ_API_KEY=gsk_your_key_here
```

Or create `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "gsk_your_key_here"
```

**4. Run the app**
```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## 🔥 Persistent Memory with Firestore

By default, memory and chat history reset whenever the app restarts (see
**Notes on Persistence** below). To make them survive redeploys, connect a
Firebase Firestore database.

**1. Create a Firebase project**
Go to [console.firebase.google.com](https://console.firebase.google.com) → **Add project**. Then enable **Firestore Database** (Build → Firestore Database → Create database, start in production mode).

**2. Create a service account key**
Project settings → **Service accounts** → **Generate new private key**. This downloads a JSON file — keep it secret, never commit it.

**3. Add it to Streamlit secrets**
Open the downloaded JSON and copy its fields into `.streamlit/secrets.toml` (locally) or the **Secrets** panel (Streamlit Cloud) under a `[firebase]` table:

```toml
GROQ_API_KEY = "gsk_your_key_here"

[firebase]
type = "service_account"
project_id = "your-project-id"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "firebase-adminsdk-...@your-project-id.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"
```

> The `private_key` must keep its `\n` line breaks exactly as in the downloaded JSON — TOML needs them written as literal `\n` inside the quoted string, not real newlines.

**4. Install the dependency and run**
```bash
pip install firebase-admin
streamlit run app.py
```

**How it works:** there's no login system. Instead, each visit gets a random session ID appended to the URL (`?uid=...`) the first time the app loads. That ID is the Firestore document key for that person's memory + chat history. **Bookmark or save the URL with the `uid` in it** to return to the same data later — a fresh URL means fresh (empty) memory. The sidebar's **🔗 Session** section shows the current ID and confirms whether Firestore is actually connected (it falls back to session-only memory automatically if secrets aren't configured, so the app still runs without Firebase set up).

If you'd rather have real accounts instead of a bookmarkable link (so memory follows a person across devices without needing the URL), the next step up is adding **Firebase Authentication** — let me know if you want that wired in too.

---

## ☁️ Deploying to Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and create a new app pointing at `app.py`.
3. In **App settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```
4. Deploy. The app reads the key from `st.secrets` automatically — no code changes needed.

---

## 🧭 Using the App

| Action | How |
|---|---|
| **Chat** | Type in the input box at the bottom and press Enter. |
| **Switch persona** | Click any persona button in the sidebar — the active one highlights in orange, and a confirmation toast appears. |
| **Upload a PDF** | Use the sidebar file uploader; a banner confirms it's loaded, and you can immediately ask questions about it. |
| **Change model** | Pick from the sidebar dropdown — quality vs. speed tradeoff. |
| **View/clear memory** | Remembered facts show in the sidebar; clear them with **🗑️ Clear Memory**. |
| **Clear chat** | **🗑 Clear Chat** resets the conversation (keeps memory). |
| **Export chat** | **💾 Export** downloads the conversation as JSON. |

---

## ⚠️ Notes on Persistence

- **Conversation history** lives in `st.session_state` — it resets when the browser tab is refreshed or the session ends.
- **Memory** (name, major, etc.) and **chat history** are written to Firestore when `[firebase]` secrets are configured (see **Persistent Memory with Firestore** above) — this survives redeploys and restarts, keyed to the `uid` in the page URL. Without Firestore configured, memory falls back to a local JSON file (`campusmind_memory.json`) that survives a refresh but resets on redeploys, since Streamlit Community Cloud's filesystem is ephemeral.
- **Personas** are stored on the `Chatbot` instance inside `st.session_state`, so they're isolated per user session and won't leak between visitors.

---

## 🩺 Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| "API key not set" error | `GROQ_API_KEY` missing | Set it via environment variable (local) or `st.secrets` (cloud). |
| `⚠️ Rate limit reached` | Too many requests in a short window | Wait a few seconds; consider switching to `llama-3.1-8b-instant`. |
| PDF upload fails / empty context | Scanned/image-only PDF with no extractable text | Use a text-based PDF, or OCR it first. |
| Persona button doesn't seem to change tone | Very short/simple prompt where personas behave similarly | Ask something persona-specific (e.g. a coding question for Python Tutor) to see the difference clearly. |
| Voice input/output not visible in UI | Backend methods (`transcribe_audio`, `text_to_speech`) exist but aren't yet wired to a mic widget | Add an audio input component (e.g. `streamlit-mic-recorder`) and call `bot.transcribe_audio()` on the captured bytes. |

---

## 👤 Author

Built by **Aazan Khan** — BS Computer Science student at International Islamic University Islamabad (IIUI), focused on Generative AI application development.
