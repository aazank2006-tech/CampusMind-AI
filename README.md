# 🎓 CampusMind AI

An intelligent campus assistant powered by [Groq](https://console.groq.com) + Streamlit.

## Features
| Feature | Details |
|---|---|
| 🧠 Persistent Memory | Remembers your name, major, university across sessions |
| 📄 PDF Upload | Upload any PDF and ask questions about it |
| 🎙️ Voice Input | Speak your message — transcribed by Groq Whisper |
| 🔊 Voice Output | Hear replies read aloud via gTTS |
| 🎭 5 Personas | Campus assistant, Python tutor, writing coach, and more |
| ⚡ Fast Inference | Free Groq API — blazing fast LLaMA & Mixtral models |

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/campusmind-ai.git
cd campusmind-ai
pip install -r requirements.txt
export GROQ_API_KEY="gsk_..."
streamlit run app.py
```

## Deploy to Streamlit Cloud

1. Push to GitHub
2. Go to share.streamlit.io → New app → select repo
3. Main file: `app.py`
4. Secrets → add: `GROQ_API_KEY = "gsk_your_key"`
5. Deploy ✅

## File Structure
```
campusmind-ai/
├── app.py                  ← Streamlit UI
├── chatbot.py              ← Groq logic + memory + voice
├── requirements.txt
├── .streamlit/
│   ├── config.toml         ← Dark theme
│   └── secrets.toml        ← API key (gitignored)
└── .gitignore
```
