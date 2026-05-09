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

# ── Inject font preconnect in head via components ─────────────
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

st.markdown("""
<style>

/* ════════════════════════════════════════
   FONT — Sora with fallback stack
   ════════════════════════════════════════ */
*, *::before, *::after {
    box-sizing: border-box;
    font-family: 'Sora', -apple-system, 'Segoe UI', system-ui, sans-serif !important;
}

body, .stApp, .stApp * {
    background-color: #0d0f14;
    color: #d4d8e8;
}

/* Force Sora everywhere Streamlit overrides */
.stApp, .stApp p, .stApp span, .stApp div,
.stApp input, .stApp textarea, .stApp button,
.stApp label, .stApp select {
    font-family: 'Sora', -apple-system, 'Segoe UI', system-ui, sans-serif !important;
}

/* ════════════════════════════════════════
   SIDEBAR — smooth slide
   ════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: #13151d !important;
    border-right: 1px solid #1e2130 !important;
    min-width: 240px !important;
    max-width: 240px !important;
    overflow: hidden !important;
    transition:
        min-width 0.35s cubic-bezier(0.4, 0, 0.2, 1),
        max-width 0.35s cubic-bezier(0.4, 0, 0.2, 1),
        border-color 0.35s ease !important;
}
section[data-testid="stSidebar"][aria-expanded="false"] {
    min-width: 0px !important;
    max-width: 0px !important;
    border-right-color: transparent !important;
}
section[data-testid="stSidebar"] > div {
    padding: 1rem 0.8rem !important;
    opacity: 1 !important;
    transition: opacity 0.2s ease 0.05s !important;
    width: 240px !important;
}
section[data-testid="stSidebar"][aria-expanded="false"] > div {
    opacity: 0 !important;
    pointer-events: none !important;
}

/* ── Sidebar content ── */
.sb-title {
    font-size: 1rem;
    font-weight: 700;
    color: #f1f3fa;
    padding-bottom: 12px;
    border-bottom: 1px solid #1e2130;
    margin-bottom: 14px;
    letter-spacing: -0.3px;
}
.sb-label {
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #3a405e;
    margin: 16px 0 7px;
}
.sb-status-ok {
    background: #0a1f15; border: 1px solid #1a5c38;
    border-radius: 8px; padding: 6px 10px;
    font-size: 0.76rem; color: #4ade80; font-weight: 600;
}
.sb-status-err {
    background: #1a0a0a; border: 1px solid #5c1a1a;
    border-radius: 8px; padding: 6px 10px;
    font-size: 0.76rem; color: #f87171; font-weight: 600;
}

section[data-testid="stSidebar"] .stSelectbox > div > div {
    background: #0d0f14 !important;
    border: 1px solid #252a3d !important;
    border-radius: 8px !important;
    color: #d4d8e8 !important;
    font-size: 0.8rem !important;
}
section[data-testid="stSidebar"] label {
    color: #3a405e !important;
    font-size: 0.6rem !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
}
section[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    background: #0d0f14 !important;
    border: 1px solid #1e2130 !important;
    color: #7880a4 !important;
    border-radius: 8px !important;
    font-size: 0.76rem !important;
    font-weight: 500 !important;
    padding: 0.4rem 0.7rem !important;
    margin-bottom: 4px !important;
    text-align: left !important;
    transition: all 0.15s ease !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    border-color: #4a5af0 !important;
    color: #9da8ff !important;
    background: #111428 !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: #0d0f14 !important;
    border: 1px dashed #252a3d !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] p {
    color: #3a405e !important;
    font-size: 0.73rem !important;
}
section[data-testid="stSidebar"] .stToggle label {
    font-size: 0.78rem !important;
    color: #7880a4 !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
    font-weight: 500 !important;
}
.mem-item { font-size: 0.76rem; color: #7880a4; padding: 2px 0; }
.mem-item strong { color: #c8cfe8; }

/* ════════════════════════════════════════
   MAIN AREA
   ════════════════════════════════════════ */
.main .block-container {
    max-width: 100% !important;
    padding: 1.5rem 2.5rem 110px !important;
}

.chat-header {
    display: flex; align-items: center; gap: 10px;
    padding-bottom: 14px; border-bottom: 1px solid #1e2130;
    margin-bottom: 24px;
}
.chat-header h1 {
    font-size: 1.3rem; font-weight: 800;
    color: #f1f3fa; margin: 0; letter-spacing: -0.5px;
}

/* Chat bubbles */
.msg-row {
    display: flex; align-items: flex-start;
    gap: 10px; margin-bottom: 18px;
}
.msg-row.user { flex-direction: row-reverse; }
.avatar-wrap {
    width: 32px; height: 32px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.82rem; font-weight: 700; flex-shrink: 0;
}
.av-bot  { background: #1e2130; color: #c8cfe8; }
.av-user { background: #2d3ec8; color: #fff; }

.bubble {
    max-width: 72%; padding: 11px 15px; border-radius: 12px;
    font-size: 0.86rem; line-height: 1.7;
    white-space: pre-wrap; word-break: break-word;
}
.bubble-bot {
    background: #13151d; border: 1px solid #1e2130;
    border-radius: 4px 12px 12px 12px; color: #d4d8e8;
}
.bubble-user {
    background: #1c2b82; border: 1px solid #2b3fb0;
    border-radius: 12px 4px 12px 12px; color: #dde3ff;
}

/* Empty state */
.empty-wrap { text-align: center; padding: 80px 20px 40px; }
.empty-wrap .icon { font-size: 3rem; margin-bottom: 14px; }
.empty-wrap h2 {
    font-size: 1.2rem; color: #7880a4; margin: 0;
    font-weight: 700; letter-spacing: -0.3px;
}

/* PDF banner */
.pdf-banner {
    background: #0b1526; border: 1px solid #1a3660;
    border-radius: 8px; padding: 8px 14px;
    font-size: 0.79rem; color: #6ea8ff; margin-bottom: 18px;
}

/* ════════════════════════════════════════
   CHAT INPUT — styled, above Manage App
   JS will handle left offset transition
   ════════════════════════════════════════ */
[data-testid="stChatInput"] {
    position: fixed !important;
    /* bottom: 48px puts it above the ~40px Streamlit "Manage app" bar */
    bottom: 48px !important;
    right: 0 !important;
    /* left is set dynamically by JS below */
    z-index: 9999 !important;
    background: #0d0f14 !important;
    border-top: 1px solid #1e2130 !important;
    padding: 10px 18px 12px !important;
    margin: 0 !important;
    /* transition applied via JS-injected style */
}
[data-testid="stChatInput"] > div {
    max-width: 100% !important;
    margin: 0 !important;
    background: #13151d !important;
    border: 1px solid #252a3d !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 32px rgba(0,0,0,0.4) !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: #3346c8 !important;
    box-shadow: 0 0 0 3px rgba(51,70,200,0.18), 0 4px 32px rgba(0,0,0,0.4) !important;
}
[data-testid="stChatInputTextArea"] {
    background: transparent !important;
    border: none !important;
    color: #d4d8e8 !important;
    font-size: 0.9rem !important;
    font-weight: 400 !important;
    box-shadow: none !important;
    resize: none !important;
    letter-spacing: -0.1px !important;
}
[data-testid="stChatInputTextArea"]::placeholder {
    color: #2e344f !important;
    font-style: italic !important;
}
[data-testid="stChatInput"] button[kind="primaryFormSubmit"],
[data-testid="stChatInput"] button {
    background: #3346c8 !important;
    border-radius: 10px !important;
    border: none !important;
    transition: background 0.15s ease, transform 0.1s ease !important;
}
[data-testid="stChatInput"] button:hover {
    background: #4558e0 !important;
    transform: scale(1.06) !important;
}

footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── JavaScript: sync input bar left with sidebar transition ───
st.markdown("""
<script>
(function() {
    const SIDEBAR_W = 240;   // px — must match CSS min/max-width
    const DURATION  = 350;   // ms — must match CSS transition duration

    function getInput() {
        return document.querySelector('[data-testid="stChatInput"]');
    }
    function getSidebar() {
        return document.querySelector('section[data-testid="stSidebar"]');
    }

    function applyLeft() {
        const input   = getInput();
        const sidebar = getSidebar();
        if (!input || !sidebar) return;

        const expanded = sidebar.getAttribute('aria-expanded') !== 'false';
        const targetLeft = expanded ? SIDEBAR_W + 'px' : '0px';

        // Apply transition + position in one shot
        input.style.transition =
            'left ' + DURATION + 'ms cubic-bezier(0.4,0,0.2,1)';
        input.style.left = targetLeft;
    }

    // Observe sidebar aria-expanded changes
    function observe() {
        const sidebar = getSidebar();
        if (!sidebar) {
            setTimeout(observe, 100);
            return;
        }
        // Run once on load
        applyLeft();

        const mo = new MutationObserver(applyLeft);
        mo.observe(sidebar, { attributes: true, attributeFilter: ['aria-expanded'] });
    }

    // Wait for DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', observe);
    } else {
        observe();
    }

    // Also re-apply after Streamlit re-renders
    window.addEventListener('load', () => setTimeout(applyLeft, 300));
})();
</script>
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
        st.caption("Set GROQ_API_KEY env var or add to Streamlit secrets.")

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
                st.markdown(
                    f'<div class="mem-item"><strong>{k.title()}:</strong> {v}</div>',
                    unsafe_allow_html=True,
                )
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
        "📊 Study Planner":    "You are CampusMind AI acting as a study planner. Help schedules, time management, and exam prep.",
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
                st.download_button(
                    "⬇ JSON", data=data,
                    file_name="campusmind_chat.json",
                    mime="application/json",
                )
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
        f'<div class="pdf-banner">📄 <strong>{st.session_state.pdf_name}</strong>'
        f' loaded — ask me anything about it!</div>',
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
