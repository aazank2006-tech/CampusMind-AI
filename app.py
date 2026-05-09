"""
app.py — CampusMind AI — Streamlit UI
Features: PDF upload, voice input/output, persistent memory, fixed sidebar.
Run: streamlit run app.py
"""

import os, json, io
import streamlit as st
from chatbot import Chatbot, AVAILABLE_MODELS, BASE_SYSTEM_PROMPT

# ── Must be FIRST Streamlit call ──────────────────────────────────────────────
st.set_page_config(
    page_title="CampusMind AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS — clean, sidebar-safe dark theme ──────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Base ── */
body, .stApp {
    background-color: #0f1117 !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background-color: #1a1d27 !important;
    border-right: 1px solid #2d3148 !important;
    min-width: 210px !important;
    max-width: 210px !important;
    transition: all 0.3s ease !important;
}
section[data-testid="stSidebar"][aria-expanded="false"] {
    min-width: 0px !important;
    max-width: 0px !important;
    overflow: hidden !important;
}
section[data-testid="stSidebar"] > div {
    padding: 0.6rem !important;
}
.main .block-container {
    max-width: 100% !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    transition: padding 0.3s ease !important;
}

/* ── Sidebar text inputs ── */
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea {
    background-color: #0f1117 !important;
    color: #e2e8f0 !important;
    border: 1px solid #2d3148 !important;
    border-radius: 8px !important;
}

/* ── Sidebar select boxes ── */
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background-color: #0f1117 !important;
    border: 1px solid #2d3148 !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}

/* ── Sidebar labels ── */
section[data-testid="stSidebar"] label {
    color: #94a3b8 !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

/* ── Sidebar buttons ── */
section[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    background: #0f1117 !important;
    border: 1px solid #2d3148 !important;
    color: #94a3b8 !important;
    border-radius: 8px !important;
    font-size: 0.75rem !important;
    padding: 0.3rem 0.6rem !important;
    margin-bottom: 3px !important;
    transition: all 0.2s !important;
    text-align: left !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    border-color: #f97316 !important;
    color: #f97316 !important;
    background: #1a1d27 !important;
}

/* ── Dividers ── */
.sidebar-divider {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #475569;
    margin: 16px 0 8px;
    padding-bottom: 6px;
    border-bottom: 1px solid #2d3148;
}

/* ── Main area ── */
.main-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 0 16px;
    border-bottom: 1px solid #2d3148;
    margin-bottom: 20px;
}
.main-header h1 {
    font-size: 1.6rem;
    font-weight: 700;
    color: #f1f5f9;
    margin: 0;
}
.badge {
    background: #f97316;
    color: #000;
    font-size: 0.6rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 20px;
    letter-spacing: 1px;
    text-transform: uppercase;
}
.memory-badge {
    background: #1e40af;
    color: #bfdbfe;
    font-size: 0.6rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 20px;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* ── Chat messages ── */
.msg-user {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 14px;
}
.msg-bot {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 14px;
}
.bubble-user {
    background: #1e3a5f;
    border: 1px solid #2563eb;
    color: #e2e8f0;
    padding: 12px 16px;
    border-radius: 16px 16px 4px 16px;
    max-width: 70%;
    font-size: 0.9rem;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
}
.bubble-bot {
    background: #1a1d27;
    border: 1px solid #2d3148;
    color: #e2e8f0;
    padding: 12px 16px;
    border-radius: 16px 16px 16px 4px;
    max-width: 70%;
    font-size: 0.9rem;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
}
.avatar {
    width: 32px; height: 32px;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.9rem; font-weight: 700;
    flex-shrink: 0; margin-top: 2px;
}
.av-user { background: #f97316; color: #000; }
.av-bot  { background: #2d3148; color: #e2e8f0; }

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #475569;
}
.empty-state .icon { font-size: 3.5rem; margin-bottom: 16px; }
.empty-state h2 { color: #94a3b8; font-size: 1.3rem; margin-bottom: 8px; }
.empty-state p  { font-size: 0.85rem; line-height: 1.7; }

/* ── Info chips ── */
.chip-row { display: flex; gap: 8px; flex-wrap: wrap; margin: 8px 0; }
.chip {
    background: #1a1d27; border: 1px solid #2d3148;
    border-radius: 20px; padding: 3px 10px;
    font-size: 0.7rem; color: #64748b;
}
.chip span { color: #f97316; font-weight: 600; }

/* ── Voice indicator ── */
.voice-hint {
    font-size: 0.75rem; color: #64748b;
    text-align: center; margin-top: 4px;
}

/* ── PDF banner ── */
.pdf-banner {
    background: #0f2027;
    border: 1px solid #1e40af;
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 0.82rem;
    color: #93c5fd;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── Hide Streamlit footer only ── */
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "messages":       [],
        "bot":            None,
        "api_key_set":    False,
        "selected_model": list(AVAILABLE_MODELS.keys())[0],
        "pdf_loaded":     False,
        "pdf_name":       "",
        "voice_text":     "",
        "tts_audio":      None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Helper: text-to-speech ────────────────────────────────────────────────────
def text_to_speech(text: str) -> bytes:
    """Convert text to audio bytes using gTTS."""
    try:
        from gtts import gTTS
        buf = io.BytesIO()
        tts = gTTS(text=text[:500], lang="en", slow=False)
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception as e:
        st.warning(f"TTS error: {e}")
        return b""


# ── Helper: PDF extraction ────────────────────────────────────────────────────
def extract_pdf_text(uploaded_file) -> str:
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        return "\n\n".join(text_parts)
    except Exception as e:
        st.error(f"PDF read error: {e}")
        return ""


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:

    st.markdown("## 🎓 CampusMind AI")
    st.markdown("---")

    # ── API Key — loaded silently from secrets/env, never shown in UI ────────
    _env_key = os.environ.get("GROQ_API_KEY", "")
    _secret_key = ""
    try:
        _secret_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        pass
    _api_key = _env_key or _secret_key

    if _api_key:
        if not st.session_state.api_key_set or st.session_state.bot is None:
            try:
                st.session_state.bot = Chatbot(
                    api_key=_api_key,
                    model=st.session_state.selected_model,
                )
                st.session_state.api_key_set = True
            except Exception as e:
                st.error(f"Bot init failed: {e}")
        st.success("✅ CampusMind AI is ready!")
    else:
        st.error(
            "⚠️ API key not configured.\n\n"
            "**For local use:** set environment variable\n"
            "`export GROQ_API_KEY=gsk_...`\n\n"
            "**For Streamlit Cloud:** go to\n"
            "Settings → Secrets → add\n"
            "`GROQ_API_KEY = \"gsk_...\"`"
        )

    # ── Model ─────────────────────────────────────────────────
    st.markdown('<div class="sidebar-divider">🤖 Model</div>', unsafe_allow_html=True)
    model_label = st.selectbox(
        "Model",
        options=list(AVAILABLE_MODELS.values()),
        index=0,
    )
    selected_model_id = [k for k, v in AVAILABLE_MODELS.items() if v == model_label][0]
    if st.session_state.bot and selected_model_id != st.session_state.selected_model:
        st.session_state.selected_model = selected_model_id
        st.session_state.bot.change_model(selected_model_id)

    # ── PDF Upload ────────────────────────────────────────────
    st.markdown('<div class="sidebar-divider">📄 PDF Upload</div>', unsafe_allow_html=True)
    uploaded_pdf = st.file_uploader("Upload a PDF", type=["pdf"], label_visibility="collapsed")

    if uploaded_pdf:
        if uploaded_pdf.name != st.session_state.pdf_name:
            with st.spinner("Reading PDF..."):
                pdf_text = extract_pdf_text(uploaded_pdf)
            if pdf_text and st.session_state.bot:
                st.session_state.bot.set_pdf_context(pdf_text)
                st.session_state.pdf_loaded = True
                st.session_state.pdf_name = uploaded_pdf.name
                st.success(f"📄 {uploaded_pdf.name} loaded!")
    else:
        if st.session_state.pdf_loaded and st.session_state.bot:
            st.session_state.bot.clear_pdf_context()
            st.session_state.pdf_loaded = False
            st.session_state.pdf_name = ""

    # ── Voice Input ───────────────────────────────────────────
    st.markdown('<div class="sidebar-divider">🎙️ Voice Input</div>', unsafe_allow_html=True)
    st.caption("Record your message — transcribed by Groq Whisper")

    try:
        from audio_recorder_streamlit import audio_recorder
        audio_bytes = audio_recorder(
            text="",
            recording_color="#f97316",
            neutral_color="#2d3148",
            icon_size="2x",
            pause_threshold=2.5,
        )
        if audio_bytes and len(audio_bytes) > 1000:
            if st.session_state.bot and st.session_state.api_key_set:
                with st.spinner("Transcribing..."):
                    transcript = st.session_state.bot.transcribe_audio(audio_bytes)
                if transcript:
                    st.session_state.voice_text = transcript
                    st.success(f"✅ Heard: *{transcript[:60]}...*" if len(transcript) > 60 else f"✅ Heard: *{transcript}*")
                else:
                    st.warning("Couldn't transcribe — try again.")
            else:
                st.warning("Enter API key first.")
    except ImportError:
        st.warning("Install `audio-recorder-streamlit` for voice input.")
        st.code("pip install audio-recorder-streamlit", language="bash")

    # ── Voice Output toggle ───────────────────────────────────
    voice_output = st.toggle("🔊 Read replies aloud", value=False)

    # ── Memory viewer ─────────────────────────────────────────
    st.markdown('<div class="sidebar-divider">🧠 Memory</div>', unsafe_allow_html=True)
    if st.session_state.bot:
        facts = st.session_state.bot.memory.get_all()
        if facts:
            for k, v in facts.items():
                st.markdown(f"**{k.title()}:** {v}")
        else:
            st.caption("Nothing remembered yet. Tell me your name!")

        if st.button("🗑️ Clear Memory"):
            st.session_state.bot.memory.clear()
            st.rerun()

    # ── Personas ──────────────────────────────────────────────
    st.markdown('<div class="sidebar-divider">🎭 Personas</div>', unsafe_allow_html=True)
    personas = {
        "🎓 Campus Assistant": BASE_SYSTEM_PROMPT,
        "🐍 Python Tutor":     "You are CampusMind AI acting as a Python tutor. Only answer coding questions. Give short code examples.",
        "✍️ Writing Coach":    "You are CampusMind AI acting as a writing coach. Help with clarity, grammar, and style.",
        "📊 Study Planner":    "You are CampusMind AI acting as a study planner. Help with schedules, time management, and exam prep.",
        "🌍 Research Helper":  "You are CampusMind AI acting as a research assistant. Help find sources, summarize topics, and structure essays.",
    }
    for label, prompt in personas.items():
        if st.button(label):
            if st.session_state.bot:
                # Patch just the base; memory block is added automatically
                from chatbot import BASE_SYSTEM_PROMPT as _base
                import chatbot as _cm
                _cm.BASE_SYSTEM_PROMPT = prompt
                st.rerun()

    # ── Controls ──────────────────────────────────────────────
    st.markdown('<div class="sidebar-divider">⚙️ Controls</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑 Clear Chat"):
            st.session_state.messages = []
            if st.session_state.bot:
                st.session_state.bot.reset()
            st.rerun()
    with col2:
        if st.button("💾 Export"):
            if st.session_state.messages:
                data = json.dumps(st.session_state.messages, indent=2)
                st.download_button("⬇ JSON", data=data,
                                   file_name="campusmind_chat.json",
                                   mime="application/json")
            else:
                st.warning("No messages yet.")

    # Stats
    if st.session_state.messages:
        turns = len(st.session_state.messages) // 2
        words = sum(len(m["content"].split()) for m in st.session_state.messages)
        st.markdown(
            f'<div class="chip-row">'
            f'<div class="chip">Turns <span>{turns}</span></div>'
            f'<div class="chip">Words <span>{words}</span></div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CHAT AREA
# ══════════════════════════════════════════════════════════════════════════════

# Header
st.markdown(
    '<div class="main-header">'
    '<span style="font-size:2rem">🎓</span>'
    '<h1>CampusMind AI</h1>'
    '</div>',
    unsafe_allow_html=True,
)

# PDF context banner
if st.session_state.pdf_loaded:
    st.markdown(
        f'<div class="pdf-banner">📄 <strong>{st.session_state.pdf_name}</strong> is loaded — ask me anything about it!</div>',
        unsafe_allow_html=True,
    )

# TTS audio playback (shown above chat if available)
if st.session_state.tts_audio:
    st.audio(st.session_state.tts_audio, format="audio/mp3", autoplay=True)
    st.session_state.tts_audio = None

# Messages
if not st.session_state.messages:
    st.markdown("""
    <div class="empty-state">
        <div class="icon">🎓</div>
        <h2>Welcome to CampusMind AI</h2>
        <p>
            Your intelligent campus companion.<br>
            I remember your name, major, and preferences across sessions.<br>
            Upload a PDF 📄 · Use your voice 🎙️ · Ask me anything!
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        is_user = msg["role"] == "user"
        if is_user:
            st.markdown(
                f'<div class="msg-user">'
                f'<div class="bubble-user">{msg["content"]}</div>'
                f'<div class="avatar av-user" style="margin-left:8px">U</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="msg-bot">'
                f'<div class="avatar av-bot" style="margin-right:8px">🎓</div>'
                f'<div class="bubble-bot">{msg["content"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ── Input row ────────────────────────────────────────────────
# Pre-fill from voice if available
voice_prefill = st.session_state.pop("voice_text", "") if "voice_text" in st.session_state else ""

prompt = st.chat_input(
    "Type your message… (or use 🎙️ voice in the sidebar)",
    disabled=not st.session_state.api_key_set,
)

# Use voice transcript if no typed input
final_input = prompt or (st.session_state.get("voice_text", "") if not prompt else "")

# Clear voice_text after use
if st.session_state.get("voice_text") and not prompt:
    final_input = st.session_state.voice_text
    st.session_state.voice_text = ""

if final_input and st.session_state.bot:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.spinner("CampusMind AI is thinking..."):
        reply = st.session_state.bot.chat(final_input)
    st.session_state.messages.append({"role": "assistant", "content": reply})

    # TTS if enabled
    if voice_output:
        with st.spinner("Generating voice response..."):
            audio = text_to_speech(reply)
            if audio:
                st.session_state.tts_audio = audio

    st.rerun()
