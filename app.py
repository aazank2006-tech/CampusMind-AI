"""
app.py — CampusMind AI — Streamlit UI
"""

import os, json, io
import streamlit as st
from chatbot import Chatbot, AVAILABLE_MODELS, BASE_SYSTEM_PROMPT

st.set_page_config(
    page_title="CampusMind AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

body, .stApp {
    background: #0d0f14 !important;
    color: #d4d8e8 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Sidebar with smooth slide transition ── */
section[data-testid="stSidebar"] {
    background: #13151d !important;
    border-right: 1px solid #1e2130 !important;
    min-width: 220px !important;
    max-width: 220px !important;
    transition: min-width 0.3s cubic-bezier(0.4,0,0.2,1),
                max-width 0.3s cubic-bezier(0.4,0,0.2,1),
                border-color 0.3s ease !important;
    overflow: hidden !important;
}
section[data-testid="stSidebar"][aria-expanded="false"] {
    min-width: 0px !important;
    max-width: 0px !important;
    border-right-color: transparent !important;
}
section[data-testid="stSidebar"] > div {
    padding: 1rem 0.75rem !important;
    opacity: 1;
    transition: opacity 0.2s ease !important;
}
section[data-testid="stSidebar"][aria-expanded="false"] > div {
    opacity: 0 !important;
    pointer-events: none !important;
}

/* Main content transitions with sidebar */
.main .block-container {
    max-width: 100% !important;
    padding: 1.5rem 2.5rem 90px !important;
    transition: padding 0.3s cubic-bezier(0.4,0,0.2,1) !important;
}

/* ── Sidebar elements ── */
.sb-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 1rem;
    font-weight: 700;
    color: #f1f3fa;
    padding-bottom: 12px;
    border-bottom: 1px solid #1e2130;
    margin-bottom: 16px;
    letter-spacing: -0.2px;
}
.sb-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #3d4260;
    margin: 18px 0 8px;
}
.sb-status-ok {
    display: flex; align-items: center; gap: 6px;
    background: #0d2218; border: 1px solid #1a5c38;
    border-radius: 8px; padding: 7px 10px;
    font-size: 0.78rem; color: #4ade80; font-weight: 600;
}
.sb-status-err {
    display: flex; align-items: center; gap: 6px;
    background: #1f0d0d; border: 1px solid #5c1a1a;
    border-radius: 8px; padding: 7px 10px;
    font-size: 0.78rem; color: #f87171; font-weight: 600;
}
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background: #0d0f14 !important;
    border: 1px solid #1e2130 !important;
    border-radius: 8px !important;
    color: #d4d8e8 !important;
    font-size: 0.82rem !important;
}
section[data-testid="stSidebar"] label {
    color: #3d4260 !important;
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
}
section[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    background: #0d0f14 !important;
    border: 1px solid #1e2130 !important;
    color: #8891b4 !important;
    border-radius: 8px !important;
    font-size: 0.78rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    padding: 0.45rem 0.75rem !important;
    margin-bottom: 4px !important;
    text-align: left !important;
    transition: all 0.15s ease !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    border-color: #5b6af0 !important;
    color: #a5b0ff !important;
    background: #13152a !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    background: transparent !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: #0d0f14 !important;
    border: 1px dashed #1e2130 !important;
    border-radius: 8px !important;
    padding: 12px !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] p {
    color: #3d4260 !important;
    font-size: 0.75rem !important;
}
section[data-testid="stSidebar"] .stToggle { margin-top: 4px !important; }
section[data-testid="stSidebar"] .stToggle label {
    font-size: 0.78rem !important; color: #8891b4 !important;
    text-transform: none !important; letter-spacing: 0 !important;
    font-weight: 500 !important;
}
.mem-item { font-size: 0.78rem; color: #8891b4; padding: 2px 0; }
.mem-item strong { color: #d4d8e8; }

/* ── Header ── */
.chat-header {
    display: flex; align-items: center; gap: 10px;
    padding-bottom: 14px; border-bottom: 1px solid #1e2130;
    margin-bottom: 24px;
}
.chat-header h1 {
    font-size: 1.25rem; font-weight: 700;
    color: #f1f3fa; margin: 0; letter-spacing: -0.3px;
}

/* ── Chat messages ── */
.msg-row {
    display: flex; align-items: flex-start;
    gap: 10px; margin-bottom: 20px;
}
.msg-row.user { flex-direction: row-reverse; }
.avatar-wrap {
    width: 32px; height: 32px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem; font-weight: 700; flex-shrink: 0;
}
.av-bot  { background: #1e2130; color: #d4d8e8; }
.av-user { background: #3346c8; color: #fff; }
.bubble {
    max-width: 72%; padding: 11px 15px; border-radius: 12px;
    font-size: 0.875rem; line-height: 1.65;
    white-space: pre-wrap; word-break: break-word;
}
.bubble-bot {
    background: #13151d; border: 1px solid #1e2130;
    border-radius: 4px 12px 12px 12px; color: #d4d8e8;
}
.bubble-user {
    background: #1e2f8a; border: 1px solid #2d45c0;
    border-radius: 12px 4px 12px 12px; color: #e8ecff;
}

/* ── Empty state — icon + title only ── */
.empty-wrap {
    text-align: center;
    padding: 80px 20px 40px;
}
.empty-wrap .icon { font-size: 3rem; margin-bottom: 14px; }
.empty-wrap h2 { font-size: 1.15rem; color: #8891b4; margin: 0; }

/* ── PDF banner ── */
.pdf-banner {
    background: #0c1628; border: 1px solid #1e3d70;
    border-radius: 8px; padding: 8px 14px;
    font-size: 0.8rem; color: #7eb3ff; margin-bottom: 18px;
}

/* ══════════════════════════════════════════════════
   FULL-WIDTH FIXED INPUT BAR — left:0 to right:0
   ══════════════════════════════════════════════════ */
[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 0 !important;
    left: 0 !important;
    right: 0 !important;
    z-index: 999 !important;
    background: #0d0f14 !important;
    border-top: 1px solid #1e2130 !important;
    padding: 12px 20px 14px !important;
    margin: 0 !important;
}
[data-testid="stChatInput"] > div {
    max-width: 100% !important;
    margin: 0 !important;
    background: #13151d !important;
    border: 1px solid #1e2130 !important;
    border-radius: 12px !important;
    box-shadow: none !important;
}
[data-testid="stChatInputTextArea"] {
    background: transparent !important;
    border: none !important;
    color: #d4d8e8 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
    box-shadow: none !important;
    resize: none !important;
}
[data-testid="stChatInputTextArea"]::placeholder { color: #3d4260 !important; }
[data-testid="stChatInput"] button {
    background: #3346c8 !important;
    border-radius: 8px !important;
    border: none !important;
    transition: background 0.15s ease !important;
}
[data-testid="stChatInput"] button:hover { background: #4558e0 !important; }

footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Session state ──────────────────────────────────────────────
def init_state():
    defaults = {
        "messages":       [],
        "bot":            None,
        "api_key_set":    False,
        "selected_model": list(AVAILABLE_MODELS.keys())[0],
        "pdf_loaded":     False,
        "pdf_name":       "",
        "tts_audio":      None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Helpers ────────────────────────────────────────────────────
def text_to_speech(text: str) -> bytes:
    try:
        from gtts import gTTS
        buf = io.BytesIO()
        gTTS(text=text[:500], lang="en", slow=False).write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception as e:
        st.warning(f"TTS error: {e}")
        return b""


def extract_pdf_text(uploaded_file) -> str:
    try:
        import pdfplumber
        parts = []
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    parts.append(t)
        return "\n\n".join(parts)
    except Exception as e:
        st.error(f"PDF read error: {e}")
        return ""


# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:

    st.markdown('<div class="sb-title">🎓 CampusMind AI</div>', unsafe_allow_html=True)

    # ── API Key ───────────────────────────────────────────────
    _env_key    = os.environ.get("GROQ_API_KEY", "")
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
                st.markdown(f'<div class="sb-status-err">✗ Init failed: {e}</div>', unsafe_allow_html=True)
        st.markdown('<div class="sb-status-ok">✓ CampusMind AI is ready!</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="sb-status-err">✗ GROQ_API_KEY not set</div>', unsafe_allow_html=True)
        st.caption("Set `GROQ_API_KEY` env var or add to Streamlit secrets.")

    # ── Model selector ────────────────────────────────────────
    st.markdown('<div class="sb-label">Model</div>', unsafe_allow_html=True)
    _ml = st.selectbox(
        "Model",
        options=list(AVAILABLE_MODELS.values()),
        index=list(AVAILABLE_MODELS.keys()).index(st.session_state.selected_model),
        key="sidebar_model_sel",
        label_visibility="collapsed",
    )
    _mid = [k for k, v in AVAILABLE_MODELS.items() if v == _ml][0]
    if st.session_state.bot and _mid != st.session_state.selected_model:
        st.session_state.selected_model = _mid
        st.session_state.bot.change_model(_mid)

    # ── PDF Upload ────────────────────────────────────────────
    st.markdown('<div class="sb-label">PDF Upload</div>', unsafe_allow_html=True)
    uploaded_pdf = st.file_uploader(
        "PDF", type=["pdf"], key="main_pdf", label_visibility="collapsed"
    )
    if uploaded_pdf:
        if uploaded_pdf.name != st.session_state.pdf_name:
            with st.spinner("Reading PDF…"):
                pdf_text = extract_pdf_text(uploaded_pdf)
            if pdf_text and st.session_state.bot:
                st.session_state.bot.set_pdf_context(pdf_text)
                st.session_state.pdf_loaded = True
                st.session_state.pdf_name   = uploaded_pdf.name
    else:
        if st.session_state.pdf_loaded and st.session_state.bot:
            st.session_state.bot.clear_pdf_context()
            st.session_state.pdf_loaded = False
            st.session_state.pdf_name   = ""

    # ── TTS ───────────────────────────────────────────────────
    voice_output = st.toggle("🔊 Read replies aloud", value=False, key="main_tts")

    # ── Memory ────────────────────────────────────────────────
    st.markdown('<div class="sb-label">Memory</div>', unsafe_allow_html=True)
    if st.session_state.bot:
        facts = st.session_state.bot.memory.get_all()
        if facts:
            for k, v in facts.items():
                st.markdown(f'<div class="mem-item"><strong>{k.title()}:</strong> {v}</div>', unsafe_allow_html=True)
        else:
            st.caption("Nothing remembered yet. Tell me your name!")
        if st.button("🗑️ Clear Memory"):
            st.session_state.bot.memory.clear()
            st.rerun()

    # ── Personas ──────────────────────────────────────────────
    st.markdown('<div class="sb-label">Personas</div>', unsafe_allow_html=True)
    personas = {
        "🎓 Campus Assistant": BASE_SYSTEM_PROMPT,
        "🐍 Python Tutor":     "You are CampusMind AI acting as a Python tutor. Only answer coding questions. Give short code examples.",
        "✍️ Writing Coach":    "You are CampusMind AI acting as a writing coach. Help with clarity, grammar, and style.",
        "📊 Study Planner":    "You are CampusMind AI acting as a study planner. Help with schedules, time management, and exam prep.",
        "🌍 Research Helper":  "You are CampusMind AI acting as a research assistant. Help find sources, summarize topics, and structure essays.",
    }
    for label, sys_prompt in personas.items():
        if st.button(label, key=f"persona_{label}"):
            if st.session_state.bot:
                import chatbot as _cm
                _cm.BASE_SYSTEM_PROMPT = sys_prompt
                st.rerun()

    # ── Controls ──────────────────────────────────────────────
    st.markdown('<div class="sb-label">Controls</div>', unsafe_allow_html=True)
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


# ══════════════════════════════════════════════════════════════
# MAIN CHAT AREA
# ══════════════════════════════════════════════════════════════

st.markdown(
    '<div class="chat-header">'
    '<span style="font-size:1.6rem">🎓</span>'
    '<h1>CampusMind AI</h1>'
    '</div>',
    unsafe_allow_html=True,
)

if st.session_state.pdf_loaded:
    st.markdown(
        f'<div class="pdf-banner">📄 <strong>{st.session_state.pdf_name}</strong> loaded — ask me anything about it!</div>',
        unsafe_allow_html=True,
    )

if st.session_state.tts_audio:
    st.audio(st.session_state.tts_audio, format="audio/mp3", autoplay=True)
    st.session_state.tts_audio = None

if not st.session_state.messages:
    st.markdown("""
    <div class="empty-wrap">
        <div class="icon">🎓</div>
        <h2>Welcome to CampusMind AI</h2>
    </div>
    """, unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        is_user = msg["role"] == "user"
        if is_user:
            st.markdown(
                f'<div class="msg-row user">'
                f'<div class="avatar-wrap av-user">U</div>'
                f'<div class="bubble bubble-user">{msg["content"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="msg-row">'
                f'<div class="avatar-wrap av-bot">🎓</div>'
                f'<div class="bubble bubble-bot">{msg["content"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ── Chat Input ────────────────────────────────────────────────
prompt = st.chat_input(
    "Type your message…",
    disabled=not st.session_state.api_key_set,
)

if prompt and st.session_state.bot:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("CampusMind AI is thinking…"):
        reply = st.session_state.bot.chat(prompt)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    if voice_output:
        with st.spinner("Generating audio…"):
            audio = text_to_speech(reply)
            if audio:
                st.session_state.tts_audio = audio
    st.rerun()
