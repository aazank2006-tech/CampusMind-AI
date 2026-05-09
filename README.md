# 🎓 CampusMind AI — Streamlit App

A fast, free AI chatbot powered by [Groq](https://console.groq.com) and deployed with [Streamlit](https://streamlit.io).

## Features
- 🆓 Free Groq API (no credit card)
- ⚡ Blazing fast LLaMA / Mixtral inference
- 🎭 5 built-in personas + custom system prompt
- 🔄 Switch models mid-conversation
- 💾 Export conversation as JSON
- 🌙 Dark theme UI

---

## Run Locally

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/campusmind-ai.git
cd campusmind-ai

# 2. Install
pip install -r requirements.txt

# 3. Set API key (get free at console.groq.com)
export GROQ_API_KEY="gsk_..."

# 4. Run
streamlit run app.py
```
App opens at **http://localhost:8501**

---

## Deploy to Streamlit Cloud (Free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select your repo and set **Main file path** to `app.py`
4. Click **Advanced settings → Secrets** and add:
   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```
5. Click **Deploy** — live URL in ~2 minutes ✅

---

## File Structure

```
campusmind-ai/
├── app.py                    ← Streamlit UI
├── chatbot.py                ← Groq API logic
├── requirements.txt          ← Dependencies
├── .streamlit/
│   ├── config.toml           ← Theme settings
│   └── secrets.toml          ← API key (local only, gitignored)
├── .gitignore
└── README.md
```

---

## Customise

**Add a new persona** — in `app.py`, add to the `personas` dict:
```python
"🧑‍⚕️ Doctor": "You are a medical assistant. Always recommend consulting a real doctor."
```

**Change default model** — in `chatbot.py`:
```python
DEFAULT_MODEL = "llama-3.1-8b-instant"   # fastest
```

**Longer memory** — in `chatbot.py`:
```python
MAX_HISTORY_TURNS = 40
```
