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

# ── Claude-style unified input bar ──────────────────────────
# CSS: hide default file uploader ugliness, style everything into one bar
st.markdown("""
<style>
/* ── Scroll padding so messages don't hide behind fixed bar ── */
section.main > div { padding-bottom: 160px !important; }

/* ── The unified input container ── */
.input-box-wrapper {
    position: fixed;
    bottom: 0;
    left: 0; right: 0;
    z-index: 1000;
    background: #0f1117;
    padding: 12px 24px 16px;
    border-top: 1px solid #1e2030;
}
.input-box-inner {
    max-width: 860px;
    margin: 0 auto;
    background: #1a1d27;
    border: 1px solid #2d3148;
    border-radius: 16px;
    padding: 10px 14px 8px;
}
/* Top row: pills */
.input-top-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
    flex-wrap: wrap;
}
.pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #252a3a;
    border: 1px solid #2d3148;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.75rem;
    color: #94a3b8;
    cursor: pointer;
    transition: border-color 0.2s;
    white-space: nowrap;
}
.pill:hover { border-color: #f97316; color: #f97316; }
.pill.active { border-color: #f97316; color: #f97316; background: #2a1f0e; }

/* Bottom row: icons */
.input-bottom-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 6px;
    padding-top: 6px;
    border-top: 1px solid #252a3a;
}
.icon-btn {
    background: none; border: none;
    color: #64748b; font-size: 1.1rem;
    cursor: pointer; padding: 4px 8px;
    border-radius: 8px; transition: all 0.2s;
    display: inline-flex; align-items: center; gap: 4px;
}
.icon-btn:hover { color: #f97316; background: #252a3a; }
.icon-btn.active { color: #f97316; }
.icon-right { display: flex; align-items: center; gap: 6px; }
.tts-label { font-size: 0.72rem; color: #64748b; }

/* ── Override chat_input to blend into our box ── */
[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 88px !important;
    left: 0 !important; right: 0 !important;
    z-index: 1001 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 24px !important;
    max-width: 100% !important;
}
[data-testid="stChatInput"] > div {
    max-width: 860px !important;
    margin: 0 auto !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    padding: 0 !important;
}
[data-testid="stChatInputTextArea"] {
    background: transparent !important;
    border: none !important;
    color: #e2e8f0 !important;
    font-size: 0.93rem !important;
    padding: 4px 0 !important;
    resize: none !important;
    box-shadow: none !important;
}
[data-testid="stChatInputTextArea"]::placeholder { color: #475569 !important; }
[data-testid="stChatInput"] button {
    background: #f97316 !important;
    border-radius: 8px !important;
    border: none !important;
}

/* Hide file uploader default UI, show only what we render */
[data-testid="stFileUploader"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}
[data-testid="stFileUploader"] > div { display: none !important; }
[data-testid="stFileUploader"] section { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Hidden file uploader (triggered by paperclip pill click) ─
# We render a real st.file_uploader but hide it with CSS;
# showing a styled pill instead that triggers it via JS label click.
uploaded_pdf = st.file_uploader(
    "📎 Attach PDF", type=["pdf"],
    label_visibility="visible", key="main_pdf"
)
if uploaded_pdf:
    if uploaded_pdf.name != st.session_state.pdf_name:
        with st.spinner("Reading PDF..."):
            pdf_text = extract_pdf_text(uploaded_pdf)
        if pdf_text and st.session_state.bot:
            st.session_state.bot.set_pdf_context(pdf_text)
            st.session_state.pdf_loaded = True
            st.session_state.pdf_name = uploaded_pdf.name
else:
    if st.session_state.pdf_loaded and st.session_state.bot:
        st.session_state.bot.clear_pdf_context()
        st.session_state.pdf_loaded = False
        st.session_state.pdf_name = ""

# Current model label (short)
_model_short = {
    "llama-3.3-70b-versatile": "LLaMA 3.3 70B",
    "llama-3.1-8b-instant":    "LLaMA 3.1 8B",
    "mixtral-8x7b-32768":      "Mixtral 8x7B",
}.get(st.session_state.selected_model, st.session_state.selected_model)

# PDF pill label
_pdf_pill = f"📄 {st.session_state.pdf_name[:18]}…" if st.session_state.pdf_loaded else "📄 No PDF"
_pdf_class = "pill active" if st.session_state.pdf_loaded else "pill"

# Render the unified bottom bar (visual only — real inputs are above/below)
st.markdown(f"""
<div class="input-box-wrapper">
  <div class="input-box-inner">
    <div class="input-top-row">
      <span class="pill" onclick="document.querySelector('[data-testid=stFileUploader] input').click()">📎 Attach PDF</span>
      <span class="{_pdf_class}">{_pdf_pill}</span>
      <span class="pill">🤖 {_model_short}</span>
    </div>
    <!-- chat_input renders here via CSS positioning -->
    <div style="min-height:36px"></div>
    <div class="input-bottom-row">
      <div style="display:flex;gap:4px;align-items:center">
        <button class="icon-btn" onclick="document.querySelector('[data-testid=stFileUploader] input').click()" title="Attach PDF">📎</button>
        <button class="icon-btn" id="mic-btn" title="Voice input">🎙️</button>
      </div>
      <div class="icon-right">
        <span class="tts-label">Read aloud</span>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Model selector (hidden, controlled by pill click via JS ideally) ──
# Rendered in sidebar for now but visually shown as pill above
with st.sidebar:
    st.markdown('<div class="sidebar-divider">🤖 Model</div>', unsafe_allow_html=True)
    _ml = st.selectbox("Model", options=list(AVAILABLE_MODELS.values()),
                        index=list(AVAILABLE_MODELS.keys()).index(st.session_state.selected_model),
                        key="sidebar_model_sel")
    _mid = [k for k, v in AVAILABLE_MODELS.items() if v == _ml][0]
    if st.session_state.bot and _mid != st.session_state.selected_model:
        st.session_state.selected_model = _mid
        st.session_state.bot.change_model(_mid)

# ── Voice (mic) ───────────────────────────────────────────────
try:
    from audio_recorder_streamlit import audio_recorder
    _ab = audio_recorder(text="", recording_color="#f97316",
                         neutral_color="#475569", icon_size="sm",
                         pause_threshold=2.5, key="main_mic")
    if _ab and len(_ab) > 1000 and st.session_state.bot:
        with st.spinner("Transcribing..."):
            _tr = st.session_state.bot.transcribe_audio(_ab)
        if _tr:
            st.session_state.voice_text = _tr
except ImportError:
    pass

# ── TTS toggle ────────────────────────────────────────────────
voice_output = st.toggle("🔊 Read replies aloud", value=False, key="main_tts")

# ── Chat input ────────────────────────────────────────────────
prompt = st.chat_input(
    "Message CampusMind AI…",
    disabled=not st.session_state.api_key_set,
)

final_input = prompt
if not final_input and st.session_state.get("voice_text"):
    final_input = st.session_state.voice_text
    st.session_state.voice_text = ""

if final_input and st.session_state.bot:
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.spinner("CampusMind AI is thinking..."):
        reply = st.session_state.bot.chat(final_input)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    if voice_output:
        with st.spinner("Generating audio..."):
            audio = text_to_speech(reply)
            if audio:
                st.session_state.tts_audio = audio
    st.rerun()
