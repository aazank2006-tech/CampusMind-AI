"""
app.py — CampusMind AI — Streamlit UI
Run: streamlit run app.py
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

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;700;800&display=swap');

body, .stApp {
    background-color: #0f1117 !important;
    color: #e2e8f0 !important;
    font-family: 'DM Mono', monospace !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background-color: #1a1d27 !important;
    border-right: 1px solid #2d3148 !important;
    min-width: 240px !important;
    max-width: 240px !important;
    transition: min-width 0.4s cubic-bezier(0.4,0,0.2,1),
                max-width 0.4s cubic-bezier(0.4,0,0.2,1),
                transform  0.4s cubic-bezier(0.4,0,0.2,1) !important;
}
section[data-testid="stSidebar"][aria-expanded="false"] {
    min-width: 0px !important;
    max-width: 0px !important;
    overflow: hidden !important;
    transform: translateX(-100%) !important;
}
section[data-testid="stSidebar"] > div {
    padding: 0.8rem !important;
}
/* Main area — smooth expand when sidebar hides */
section.main {
    transition: margin-left 0.4s cubic-bezier(0.4,0,0.2,1) !important;
}
.main .block-container {
    max-width: 100% !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    transition: all 0.4s cubic-bezier(0.4,0,0.2,1) !important;
}
/* Stagger children so they reflow smoothly */
.main .block-container > * {
    transition: width 0.4s cubic-bezier(0.4,0,0.2,1) !important;
}

/* Sidebar labels */
section[data-testid="stSidebar"] label {
    color: #94a3b8 !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea {
    background-color: #0f1117 !important;
    color: #e2e8f0 !important;
    border: 1px solid #2d3148 !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background-color: #0f1117 !important;
    border: 1px solid #2d3148 !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
}
section[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    background: #0f1117 !important;
    border: 1px solid #2d3148 !important;
    color: #94a3b8 !important;
    border-radius: 8px !important;
    font-size: 0.8rem !important;
    padding: 0.35rem 0.7rem !important;
    margin-bottom: 4px !important;
    transition: all 0.2s !important;
    text-align: left !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    border-color: #f97316 !important;
    color: #f97316 !important;
}

/* Sidebar section dividers */
.sidebar-divider {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #475569;
    margin: 14px 0 8px;
    padding-bottom: 5px;
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
    font-weight: 800;
    color: #f1f5f9;
    margin: 0;
    font-family: 'Syne', sans-serif !important;
    letter-spacing: -0.5px;
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
.empty-state h2 { color: #94a3b8; font-size: 3.2rem; margin-bottom: 8px; font-family: 'Syne', sans-serif; font-weight: 800; letter-spacing: -2px; line-height: 1.1; }
.empty-state p  { font-size: 0.85rem; line-height: 1.7; }

/* ── PDF banner ── */
.pdf-banner {
    background: #0f2027;
    border: 1px solid #1e40af;
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 0.82rem;
    color: #93c5fd;
    margin-bottom: 16px;
}

/* ── Chips ── */
.chip-row { display: flex; gap: 8px; flex-wrap: wrap; margin: 8px 0; }
.chip {
    background: #0f1117; border: 1px solid #2d3148;
    border-radius: 20px; padding: 3px 10px;
    font-size: 0.7rem; color: #64748b;
}
.chip span { color: #f97316; font-weight: 600; }

/* ── Chat input ── */
[data-testid="stChatInput"] {
    max-width: 720px !important;
    margin: 0 auto !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}
[data-testid="stChatInput"] > div {
    background: #1a1d27 !important;
    border: 1px solid #2d3148 !important;
    border-radius: 10px !important;
    padding: 1px 8px !important;
}
[data-testid="stChatInputTextArea"] {
    color: #e2e8f0 !important;
    font-size: 0.88rem !important;
    min-height: 28px !important;
    max-height: 90px !important;
    padding-top: 6px !important;
    padding-bottom: 6px !important;
}
[data-testid="stChatInput"] button {
    background: #f97316 !important;
    border-radius: 8px !important;
}

footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
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


# ── Session state ─────────────────────────────────────────────────────────────
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


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🎓 CampusMind AI")
    st.markdown("---")

    # ── API Key (silent — from env or secrets) ────────────────
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
            "⚠️ API key not set.\n\n"
            "**Local:** `export GROQ_API_KEY=gsk_...`\n\n"
            "**Cloud:** Settings → Secrets → `GROQ_API_KEY = \"gsk_...\"`"
        )

    # ── Model ─────────────────────────────────────────────────
    st.markdown('<div class="sidebar-divider">🤖 Model</div>', unsafe_allow_html=True)
    model_label = st.selectbox(
        "Model", options=list(AVAILABLE_MODELS.values()),
        index=list(AVAILABLE_MODELS.keys()).index(st.session_state.selected_model),
        label_visibility="collapsed",
    )
    selected_model_id = [k for k, v in AVAILABLE_MODELS.items() if v == model_label][0]
    if st.session_state.bot and selected_model_id != st.session_state.selected_model:
        st.session_state.selected_model = selected_model_id
        st.session_state.bot.change_model(selected_model_id)

    # ── PDF Upload ────────────────────────────────────────────
    st.markdown('<div class="sidebar-divider">📄 PDF Upload</div>', unsafe_allow_html=True)
    uploaded_pdf = st.file_uploader(
        "Upload a PDF", type=["pdf"], label_visibility="collapsed"
    )
    if uploaded_pdf:
        if uploaded_pdf.name != st.session_state.pdf_name:
            with st.spinner("Reading PDF..."):
                pdf_text = extract_pdf_text(uploaded_pdf)
            if pdf_text and st.session_state.bot:
                st.session_state.bot.set_pdf_context(pdf_text)
                st.session_state.pdf_loaded = True
                st.session_state.pdf_name = uploaded_pdf.name
                st.success(f"✅ {uploaded_pdf.name[:20]} loaded!")
    else:
        if st.session_state.pdf_loaded and st.session_state.bot:
            st.session_state.bot.clear_pdf_context()
            st.session_state.pdf_loaded = False
            st.session_state.pdf_name = ""

    # ── Memory ────────────────────────────────────────────────
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
                import chatbot as _cm
                _cm.BASE_SYSTEM_PROMPT = prompt
                st.rerun()

    # ── Controls ──────────────────────────────────────────────
    st.markdown('<div class="sidebar-divider">⚙️ Controls</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑 Clear Chat"):
            st.session_state.messages = []
            if st.session_state.bot:
                st.session_state.bot.reset()
            st.rerun()
    with c2:
        if st.button("💾 Export"):
            if st.session_state.messages:
                st.download_button(
                    "⬇ JSON",
                    data=json.dumps(st.session_state.messages, indent=2),
                    file_name="campusmind_chat.json",
                    mime="application/json",
                )
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

st.markdown(
    '<div class="main-header">'
    '<span style="font-size:2rem">🎓</span>'
    '<h1>CampusMind AI</h1>'
    '</div>',
    unsafe_allow_html=True,
)

# PDF banner
if st.session_state.pdf_loaded:
    st.markdown(
        f'<div class="pdf-banner">📄 <strong>{st.session_state.pdf_name}</strong>'
        f' is loaded — ask me anything about it!</div>',
        unsafe_allow_html=True,
    )

# TTS playback
if st.session_state.tts_audio:
    st.audio(st.session_state.tts_audio, format="audio/mp3", autoplay=True)
    st.session_state.tts_audio = None

# Messages
if not st.session_state.messages:
    import random
    _greetings = [
        "How can I help you?",
        "Where should we begin?",
        "What are you working on?",
        "What's on the agenda today?",
        "What can I help you with?",
        "Ready when you are!",
        "Ask me anything.",
        "What would you like to explore today?",
    ]
    if "greeting" not in st.session_state:
        st.session_state.greeting = random.choice(_greetings)
    st.markdown(f"""
    <div class="empty-state">
        <h2>{st.session_state.greeting}</h2>
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

# ── Chat input ────────────────────────────────────────────────────────────────
prompt = st.chat_input(
    "Message CampusMind AI…",
    disabled=not st.session_state.api_key_set,
)

if prompt and st.session_state.bot:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("CampusMind AI is thinking..."):
        reply = st.session_state.bot.chat(prompt)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()
