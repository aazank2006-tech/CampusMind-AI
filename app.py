"""
app.py — CampusMind AI — Streamlit front-end powered by Groq.
Run locally:  streamlit run app.py
Deploy:       push to GitHub → connect at share.streamlit.io
"""

import json
import streamlit as st
from chatbot import Chatbot, AVAILABLE_MODELS, DEFAULT_SYSTEM_PROMPT

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="CampusMind AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;700;800&display=swap');

/* Root theme */
:root {
    --bg:        #0d0f14;
    --surface:   #161920;
    --border:    #252a35;
    --accent:    #f97316;
    --accent2:   #fb923c;
    --text:      #e8eaf0;
    --muted:     #6b7280;
    --user-bg:   #1a1f2e;
    --bot-bg:    #111318;
    --radius:    12px;
}

/* Global */
html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
}

[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

/* Header */
.chat-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 20px 0 8px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
}
.chat-header h1 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 800;
    font-size: 1.8rem;
    color: var(--text);
    margin: 0;
    letter-spacing: -0.5px;
}
.chat-header .badge {
    background: var(--accent);
    color: #000;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 20px;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* Messages */
.message-row {
    display: flex;
    gap: 14px;
    margin-bottom: 20px;
    animation: fadeUp 0.25s ease;
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.message-row.user { flex-direction: row-reverse; }

.avatar {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
}
.avatar.user-av  { background: var(--accent);  color: #000; }
.avatar.bot-av   { background: var(--border);  color: var(--text); }

.bubble {
    max-width: 72%;
    padding: 14px 18px;
    border-radius: var(--radius);
    line-height: 1.65;
    font-size: 0.9rem;
    white-space: pre-wrap;
    word-break: break-word;
}
.bubble.user-bubble {
    background: var(--user-bg);
    border: 1px solid var(--accent);
    color: var(--text);
    border-top-right-radius: 2px;
}
.bubble.bot-bubble {
    background: var(--bot-bg);
    border: 1px solid var(--border);
    color: var(--text);
    border-top-left-radius: 2px;
}

/* Input area */
.stChatInput > div {
    border: 1px solid var(--border) !important;
    background: var(--surface) !important;
    border-radius: var(--radius) !important;
}
.stChatInput textarea {
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.88rem !important;
}

/* Sidebar elements */
.stSelectbox label, .stTextArea label, .stSlider label {
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
}
.stSelectbox > div > div,
.stTextArea textarea {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.85rem !important;
    border-radius: 8px !important;
}

/* Buttons */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--muted) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.8rem !important;
    border-radius: 8px !important;
    transition: all 0.2s !important;
    width: 100%;
}
.stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}

/* Stats chips */
.stats-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin: 12px 0;
}
.stat-chip {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.72rem;
    color: var(--muted);
    font-family: 'DM Mono', monospace;
}
.stat-chip span { color: var(--accent); font-weight: 600; }

/* Empty state */
.empty-state {
    text-align: center;
    padding: 80px 20px;
    color: var(--muted);
}
.empty-state .big-icon { font-size: 3rem; margin-bottom: 16px; }
.empty-state h3 {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1.2rem;
    color: var(--text);
    margin-bottom: 8px;
}
.empty-state p { font-size: 0.85rem; line-height: 1.6; }

/* Sidebar section headers */
.sidebar-section {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 0.7rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
    margin: 20px 0 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
}

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Session state init ────────────────────────────────────────────────────────
def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []          # [{role, content}]
    if "bot" not in st.session_state:
        st.session_state.bot = None
    if "api_key_set" not in st.session_state:
        st.session_state.api_key_set = False
    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = DEFAULT_SYSTEM_PROMPT
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = list(AVAILABLE_MODELS.keys())[0]

init_state()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="chat-header"><h1>🎓 CampusMind AI</h1></div>', unsafe_allow_html=True)

    # API key input
    st.markdown('<div class="sidebar-section">API Key</div>', unsafe_allow_html=True)

    # Check Streamlit secrets first (for deployment), then env var
    import os
    env_key = os.environ.get("GROQ_API_KEY", "")
    secret_key = ""
    try:
        secret_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        pass

    prefilled = env_key or secret_key

    api_key_input = st.text_input(
        "Groq API Key",
        value=prefilled,
        type="password",
        placeholder="gsk_...",
        label_visibility="collapsed",
        help="Get your free key at console.groq.com",
    )

    if api_key_input:
        if not st.session_state.api_key_set or st.session_state.bot is None:
            try:
                st.session_state.bot = Chatbot(
                    api_key=api_key_input,
                    system_prompt=st.session_state.system_prompt,
                    model=st.session_state.selected_model,
                )
                st.session_state.api_key_set = True
            except Exception as e:
                st.error(f"Failed to init: {e}")
        st.success("✓ Connected", icon="⚡")
    else:
        st.info("Enter your Groq API key to start. Free at [console.groq.com](https://console.groq.com)")

    # Model selector
    st.markdown('<div class="sidebar-section">Model</div>', unsafe_allow_html=True)
    model_label = st.selectbox(
        "Model",
        options=list(AVAILABLE_MODELS.values()),
        index=0,
        label_visibility="collapsed",
    )
    # Map label back to model ID
    selected_model_id = [k for k, v in AVAILABLE_MODELS.items() if v == model_label][0]
    if st.session_state.bot and selected_model_id != st.session_state.selected_model:
        st.session_state.selected_model = selected_model_id
        st.session_state.bot.change_model(selected_model_id)

    # System prompt
    st.markdown('<div class="sidebar-section">Persona</div>', unsafe_allow_html=True)
    new_prompt = st.text_area(
        "System prompt",
        value=st.session_state.system_prompt,
        height=130,
        label_visibility="collapsed",
        placeholder="You are a helpful assistant...",
    )
    if new_prompt != st.session_state.system_prompt:
        st.session_state.system_prompt = new_prompt
        if st.session_state.bot:
            st.session_state.bot.change_system_prompt(new_prompt)

    # Quick personas
    st.markdown('<div class="sidebar-section">Quick Personas</div>', unsafe_allow_html=True)
    personas = {
        "🤖 Default Assistant":  DEFAULT_SYSTEM_PROMPT,
        "🐍 Python Tutor":       "You are an expert Python tutor. Only answer Python/coding questions. Give short code examples with every answer.",
        "✍️ Writing Coach":      "You are a professional writing coach. Help improve clarity, grammar, and style. Be encouraging but direct.",
        "📊 Data Analyst":       "You are a data analyst. Help with data, statistics, SQL, and visualization. Use concrete examples.",
        "🏴‍☠️ Pirate":           "You are a swashbuckling pirate. Answer every question in pirate speak. Arrr!",
    }
    for label, prompt in personas.items():
        if st.button(label, key=f"persona_{label}"):
            st.session_state.system_prompt = prompt
            if st.session_state.bot:
                st.session_state.bot.change_system_prompt(prompt)
            st.rerun()

    # Controls
    st.markdown('<div class="sidebar-section">Controls</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑 Clear chat"):
            st.session_state.messages = []
            if st.session_state.bot:
                st.session_state.bot.reset()
            st.rerun()
    with col2:
        if st.button("💾 Export"):
            if st.session_state.messages:
                export = json.dumps(st.session_state.messages, indent=2)
                st.download_button(
                    "⬇ Download JSON",
                    data=export,
                    file_name="conversation.json",
                    mime="application/json",
                )
            else:
                st.warning("No messages to export.")

    # Stats
    if st.session_state.messages:
        turns = len(st.session_state.messages) // 2
        words = sum(len(m["content"].split()) for m in st.session_state.messages)
        st.markdown(
            f'<div class="stats-row">'
            f'<div class="stat-chip">turns <span>{turns}</span></div>'
            f'<div class="stat-chip">words <span>{words}</span></div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── Main chat area ────────────────────────────────────────────────────────────
st.markdown(
    '<div class="chat-header">'
    '<h1>CampusMind AI</h1>'
    '<span class="badge">Free & Fast</span>'
    '</div>',
    unsafe_allow_html=True,
)

# Message display
chat_container = st.container()
with chat_container:
    if not st.session_state.messages:
        st.markdown("""
        <div class="empty-state">
            <div class="big-icon">🎓</div>
            <h3>Welcome to CampusMind AI</h3>
            <p>Blazing fast inference — free tier available.<br>
            Enter your API key in the sidebar to begin.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            is_user = msg["role"] == "user"
            row_class   = "user" if is_user else "bot"
            av_class    = "user-av" if is_user else "bot-av"
            bub_class   = "user-bubble" if is_user else "bot-bubble"
            avatar_icon = "U" if is_user else "⚡"

            st.markdown(
                f'<div class="message-row {row_class}">'
                f'  <div class="avatar {av_class}">{avatar_icon}</div>'
                f'  <div class="bubble {bub_class}">{msg["content"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

# Chat input (always shown at bottom)
if prompt := st.chat_input(
    "Message the chatbot...",
    disabled=not st.session_state.api_key_set,
):
    if not st.session_state.bot:
        st.error("Please enter your API key in the sidebar first.")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Get bot reply
        with st.spinner(""):
            reply = st.session_state.bot.chat(prompt)

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()
