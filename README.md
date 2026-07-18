# 🎓 CampusMind AI

**A multi-persona AI study companion for university students — built with Streamlit and the Groq API.**

![Python](https://img.shields.io/badge/python-3.9%2B-blue) ![Streamlit](https://img.shields.io/badge/streamlit-1.35%2B-red) ![Groq](https://img.shields.io/badge/powered%20by-Groq-orange) ![Status](https://img.shields.io/badge/status-student%20project-lightgrey)

### 🔗 Live App

**[https://campusmind-ai-v2-aazankhan.streamlit.app](https://campusmind-ai-v2-aazankhan.streamlit.app)**

No account or login is needed — visiting the app assigns a random session ID as a `?uid=` query parameter in the URL (`get_or_create_session_id()` in `app.py`). Bookmark the URL with your `uid` in it to come back to the same memory and chat history later (details in [Notes on Persistence](#notes-on-persistence)).

---

## 📖 Table of Contents

- [The Problem This Solves](#the-problem-this-solves)
- [Features](#features)
- [The AI Feature](#the-ai-feature)
- [Tech Stack and AI Models](#tech-stack-and-ai-models)
- [Screenshots](#screenshots)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Setup and How to Run](#setup-and-how-to-run)
- [Persistent Memory with Firestore (Optional)](#persistent-memory-with-firestore-optional)
- [Deploying to Streamlit Community Cloud](#deploying-to-streamlit-community-cloud)
- [Using the App](#using-the-app)
- [Notes on Persistence](#notes-on-persistence)
- [Troubleshooting](#troubleshooting)
- [Roadmap and Future Work](#roadmap-and-future-work)
- [Author](#author)

---

## 🎯 The Problem This Solves

University students juggle several different jobs in a single semester — write code for an assignment, get feedback on an essay, plan revision around three overlapping exam dates, dig through a 40-page lecture PDF for one definition, and figure out where to even start a research paper. In practice that means bouncing between a general chatbot, a separate PDF summarizer, a to-do app, and whatever else is open in another tab — re-explaining who you are and what course you're in every single time.

**CampusMind AI** consolidates that into one assistant with five purpose-built personas (Campus Assistant, Python Tutor, Writing Coach, Study Planner, Research Helper), each with its own behavior, plus a memory layer that quietly remembers your name, major, year, and university so you're not repeating yourself in every new chat.

**Who it's for:** university students — the primary use case is CS/STEM students at institutions like IIUI who want coding help, writing feedback, and PDF-based Q&A on lecture material in one place, but the personas generalize to any student juggling coursework across subjects.

---

## ✨ Features

**Conversation**
- Fast, multi-turn chat powered by Groq-hosted LLMs, with conversation history automatically trimmed to stay within context limits.
- Model picker — swap between `llama-3.3-70b-versatile` (best quality), `llama-3.1-8b-instant` (fastest), and `mixtral-8x7b-32768` (long context) on the fly, mid-conversation.

**Personas**
- Five switchable personas — Campus Assistant, Python Tutor, Writing Coach, Study Planner, and Research Helper — each with its own system prompt.
- Personas are scoped per browser session, so they never leak between different users.
- Switching personas gives a visible confirmation (the active one highlights in orange, plus a toast).

**Memory**
- Auto-detects and remembers your name, major, year, and university from what you type — no form to fill in.
- Remembered facts are injected into every future response so the assistant stays "in character" as your assistant, not a stranger's.
- Memory is viewable and clearable anytime from the sidebar.

**Document Q&A**
- Upload a PDF and ask questions about its contents directly in chat.
- Built-in privacy rule stops the model from surfacing names, emails, or contact details found inside the uploaded file, even if asked directly.

**Voice (backend-ready)**
- Groq Whisper transcription and gTTS speech synthesis are implemented in `chatbot.py`, ready to be wired into a mic-input UI component.

**Utility**
- Chat export — download the full conversation as JSON.
- Custom dark UI — Syne/DM Mono typography, animated collapsible sidebar, auto-scrolling chat.
- Optional Firestore-backed persistence so memory and history survive redeploys (falls back gracefully to session/local-file storage if not configured).

---

## 🧠 The AI Feature

The core AI feature is the **persona-driven conversational engine**: a Groq-hosted LLM whose system prompt is assembled fresh on every turn from three layers — the active persona, remembered facts about the student, and (optionally) uploaded document context. All quotes below are the literal strings from `chatbot.py` / `app.py`.

### 1. Base system prompt (Campus Assistant / default persona)

Defined once as `BASE_SYSTEM_PROMPT` in `chatbot.py` and reused as the default persona:

~~~text
You are CampusMind AI, a friendly and knowledgeable campus assistant.
You help students with academic questions, study tips, campus life, and general knowledge.
You are warm, encouraging, and clear in your explanations.
Always remember and use personal details the user shares (name, major, interests, university).
Keep responses concise unless the user asks for more detail.

CODE FORMATTING RULES — follow these strictly every time you write code:
- ALWAYS wrap code in markdown fenced code blocks with the correct language tag.
  Examples: ```python ... ``` or ```cpp ... ``` or ```java ... ``` or ```javascript ... ```
- ALWAYS write complete, fully working code — never truncate, never use placeholders like # ... or // rest of code here.
- ALWAYS include every import, every function, and every line needed to run the code as-is.
- For multiple snippets in one response, use a separate fenced block for each one.
- Add a brief inline comment above complex lines to explain what they do.
- If the code is long, still write it in full — never shorten or summarise it.
~~~

### 2. Persona system prompts

Each persona button in the sidebar swaps in its own short system prompt (the `PERSONAS` dict in `app.py`), replacing the base prompt for that session:

| Persona | System prompt |
|---|---|
| 🐍 Python Tutor | `You are CampusMind AI acting as a Python tutor. Only answer coding questions. Give short code examples.` |
| ✍️ Writing Coach | `You are CampusMind AI acting as a writing coach. Help with clarity, grammar, and style.` |
| 📊 Study Planner | `You are CampusMind AI acting as a study planner. Help with schedules, time management, and exam prep.` |
| 🌍 Research Helper | `You are CampusMind AI acting as a research assistant. Help find sources, summarize topics, and structure essays.` |

Persona choice lives on the `Chatbot` instance inside `st.session_state` — deliberately **not** a module-level global — so one student's active persona can never leak into another user's session on the same server process.

### 3. Rule-based memory (not an LLM call)

Memory extraction is intentionally **not** an AI step — it's a fast, deterministic pass with `re.search()` over each message (`Memory.update_from_message()` in `chatbot.py`), looking for patterns like:

- Name: `(?:my name is|i'm|i am|call me)\s+([A-Z][a-z]+(?: [A-Z][a-z]+)?)`
- Major: `(?:studying|majoring in|i study|my major is|my field is)\s+([a-zA-Z &]+?)(?:\.|,|\n|$)`
- Year: `freshman|sophomore|junior|senior|1st year|2nd year|...`
- University: `(?:at|attend|go to|from|study at)\s+([A-Z][a-zA-Z ]+?(?:University|College|Institute|School|Academy))`

Whatever is captured is saved to `Memory.facts` and rendered into a plain-text block (`to_prompt_block()`) that's prepended to the system prompt on every future turn — e.g. *"Known facts about this user: - Name: Aazan - University: IIUI"* — so the LLM stays personalized without a real extraction model in the loop.

### 4. Privacy-aware PDF grounding

When a PDF is uploaded, `pdfplumber` extracts its text and `Chatbot._system_prompt()` appends the first 6,000 characters as context, wrapped in this literal instruction block:

```
The user uploaded a document. Use it to answer questions about its academic content only.
IMPORTANT PRIVACY RULES for this document:
- NEVER mention, reveal, or repeat any person's name found in the document (teachers, professors, authors, instructors, students, or anyone else).
- NEVER reveal emails, phone numbers, office hours, room numbers, or any personal contact details.
- NEVER refer to who wrote or created the document.
- Focus ONLY on the academic subject matter, concepts, topics, and educational content.
--- DOCUMENT ---
{document text, truncated to 6000 characters}
--- END ---
```

### 5. Voice transcription

`transcribe_audio()` sends recorded audio bytes to Groq's hosted **`whisper-large-v3`** for transcription using the same Groq API key — implemented and callable, but not yet wired to a mic widget in `app.py`.

---

## 🧰 Tech Stack and AI Models

| Layer | Tool / Service | Purpose |
|---|---|---|
| UI / frontend | **Streamlit** | Chat interface, sidebar controls, session state |
| LLM inference | **Groq API** | Ultra-fast hosted inference for chat and persona behavior |
| AI models | `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768` | Quality / speed / long-context tradeoffs, user-selectable |
| Fact extraction | **Python `re` (regex)** | Rule-based, non-AI extraction of name/major/year/university from user messages |
| Speech-to-text | **Groq Whisper (`whisper-large-v3`)** | Audio transcription (backend implemented, not yet wired to a mic widget) |
| Text-to-speech | **gTTS** (Google Text-to-Speech) | Voice output (backend implemented, not yet wired to UI) |
| PDF parsing | **pdfplumber** | Extracts text from uploaded PDFs for document Q&A |
| Persistent storage | **Firebase Firestore** + `firebase-admin` | Optional cross-session persistence for memory and chat history |
| Language | **Python 3.9+** | Core application logic |
| Hosting | **Streamlit Community Cloud** | Deployment of the live app |
| Version control | **Git / GitHub** | Source control and deployment source |

---

## 📸 Screenshots

**Main chat view** — the empty-state screen with the randomized greeting and message input.

![Main chat view]
<img width="1917" height="860" alt="chat-view" src="https://github.com/user-attachments/assets/b9ad64bb-c496-4c05-a44e-8d8a5d08216c" />
)

**Memory + persona recall in action** — the sidebar shows the live session ID, model picker, PDF uploader, and remembered facts (`Name: Aazan Khan`), while the chat itself shows the model recalling that name mid-conversation.

![Sidebar memory and persona recall]<img width="1916" height="846" alt="sidebar-memory" src="https://github.com/user-attachments/assets/b7d21496-56db-4dd9-b859-2fce8af12283" />


**PDF-grounded Q&A** — a lecture PDF (`PF Lecture 16 Palindrome Function (Ex 6-5).pdf`) is loaded, and the assistant answers a question about it directly from the document, including reproducing the relevant C++ function.

![PDF question and answer]<img width="1917" height="905" alt="pdf-qa" src="https://github.com/user-attachments/assets/4f19026b-be56-4633-a896-14a753e9e700" />

---

## 📁 Project Structure

```
campusmind-ai/
├── app.py                  # Streamlit interface
├── chatbot.py              # Core chatbot logic (Groq client, memory, personas, PDF context)
├── firestore_store.py      # Firestore persistence layer (memory + chat history)
├── requirements.txt        # Python dependencies
├── .streamlit/
│   └── secrets.toml        # Local secrets template (not committed)
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

## 🚀 Setup and How to Run

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

## 🔥 Persistent Memory with Firestore (Optional)

By default, memory and chat history reset whenever the app restarts (see [Notes on Persistence](#notes-on-persistence)). To make them survive redeploys, connect a Firebase Firestore database.

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

If you'd rather have real accounts instead of a bookmarkable link (so memory follows a person across devices without needing the URL), the next step up is adding **Firebase Authentication** — see [Roadmap](#roadmap-and-future-work).

---

## ☁️ Deploying to Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and create a new app pointing at `app.py`.
3. In **App settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```
   (and the `[firebase]` block too, if you're using persistent memory)
4. Deploy. The app reads secrets from `st.secrets` automatically — no code changes needed.
5. This project is already live at the URL in [Live App](#live-app) above — if you redeploy under a new app name, update that link.

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
- **Memory** (name, major, etc.) and **chat history** are written to Firestore when `[firebase]` secrets are configured (see [Persistent Memory with Firestore](#persistent-memory-with-firestore-optional)) — this survives redeploys and restarts, keyed to the `uid` in the page URL. Without Firestore configured, memory falls back to a local JSON file (`campusmind_memory.json`) that survives a refresh but resets on redeploys, since Streamlit Community Cloud's filesystem is ephemeral.
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

## 🗺️ Roadmap and Future Work

- **Firebase Authentication** — real accounts instead of a bookmarkable session link, so memory follows a student across devices.
- **Voice mode** — wire the existing Whisper/gTTS backend into a mic-input widget in the UI.
- **Multi-document Q&A** — support asking questions across several uploaded files at once.
- **Persona customization** — let students write or tweak their own persona system prompts.

---

## 👤 Author

Built by **Aazan Khan** — BS Computer Science student at International Islamic University Islamabad (IIUI), focused on Generative AI application development.
