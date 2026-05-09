"""
app.py — CampusMind AI — Streamlit front-end powered by Groq.
Features: Chat, PDF Upload, Voice Input (Whisper), Voice Output (gTTS)
Run locally:  streamlit run app.py
Deploy:       push to GitHub → connect at share.streamlit.io
"""

import io
import os
import json
import base64
import tempfile
import streamlit as st
from chatbot import Chatbot, AVAILABLE_MODELS, DEFAULT_SYSTEM_PROMPT

# ── Page config ───────────────────────────────────────────────────────────────
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

:root {
    --bg:        #0d0f14;
    --surface:   #161920;
    --border:    #252a35;
    --accent:    #f97316;
    --text:      #e8eaf0;
    --muted:     #6b7280;
    --user-bg:   #1a1f2e;
    --bot-bg:    #111318;
    --green:     #22c55e;
    --blue:      #3b82f6;
    --radius:    12px;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
}
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

.chat-header {
    display: flex; align-items: center; gap: 12px;
    padding: 20px 0 8px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
}
.chat-header h1 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 800; font-size: 1.8rem;
    color: var(--text); margin: 0; letter-spacing: -0.5px;
}
.chat-header .badge {
    background: var(--accent); color: #000;
    font-size: 0.65rem; font-weight: 700;
    padding: 3px 8px; border-radius: 20px;
    letter-spacing: 1px; text-transform: uppercase;
}

.message-row {
    display: flex; gap: 14px; margin-bottom: 20px;
    animation: fadeUp 0.25s ease;
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.message-row.user { flex-direction: row-reverse; }

.avatar {
    width: 36px; height: 36px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0;
    font-family: 'Syne', sans-serif; font-weight: 700;
}
.avatar.user-av { background: var(--accent); color: #000; }
.avatar.bot-av  { background: var(--border); color: var(--text); }

.bubble {
    max-width: 72%; padding: 14px 18px; border-radius: var(--radius);
    line-height: 1.65; font-size: 0.9rem;
    white-space: pre-wrap; word-break: break-word;
}
.bubble.user-bubble {
    background: var(--user-bg); border: 1px solid var(--accent);
    color: var(--text); border-top-right-radius: 2px;
}
.bubble.bot-bubble {
    background: var(--bot-bg); border: 1px solid var(--border);
    color: var(--text); border-top-left-radius: 2px;
}

.pdf-banner {
    background: #1a2035; border: 1px solid var(--blue);
    border-radius: var(--radius); padding: 12px 16px;
    margin-bottom: 16px; font-size: 0.82rem; color: #93c5fd;
}
.voice-banner {
    background: #1a2a1a; border: 1px solid var(--green);
    border-radius: var(--radius); padding: 12px 16px;
    margin-bottom: 16px; font-size: 0.82rem; color: #86efac;
}

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

.stSelectbox label, .stTextArea label, .stSlider label {
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important; font-size: 0.8rem !important;
    letter-spacing: 0.5px !important; text-transform: uppercase !important;
    color: var(--muted) !important;
}
.stSelectbox > div > div, .stTextArea textarea {
    background: var(--bg) !important; border: 1px solid var(--border) !important;
    color: var(--text) !important; font-family: 'DM Mono', monospace !important;
    font-size: 0.85rem !important; border-radius: 8px !important;
}

.stButton > button {
    background: transparent !important; border: 1px solid var(--border) !important;
    color: var(--muted) !important; font-family: 'DM Mono', monospace !important;
    font-size: 0.8rem !important; border-radius: 8px !important;
    transition: all 0.2s !important; width: 100%;
}
.stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}

.stats-row { display: flex; gap: 8px; flex-wrap: wrap; margin: 12px 0; }
.stat-chip {
    background: var(--bg); border: 1px solid var(--border);
    border-radius: 20px; padding: 4px 12px;
    font-size: 0.72rem; color: var(--muted); font-family: 'DM Mono', monospace;
}
.stat-chip span { color: var(--accent); font-weight: 600; }

.empty-state { text-align: center; padding: 60px 20px; color: var(--muted); }
.empty-state .big-icon { font-size: 3rem; margin-bottom: 16px; }
.empty-state h3 {
    font-family: 'Syne', sans-serif; font-weight: 700;
    font-size: 1.2rem; color: var(--text); margin-bottom: 8px;
}
.empty-state p { font-size: 0.85rem; line-height: 1.6; }

.sidebar-section {
    font-family: 'Syne', sans-serif; font-weight: 700;
    font-size: 0.7rem; letter-spacing: 2px; text-transform: uppercase;
    color: var(--muted); margin: 20px 0 10px;
    padding-bottom: 6px; border-bottom: 1px solid var(--border);
}

#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Helper functions ──────────────────────────────────────────────────────────

def extract_pdf_text(uploaded_file) -> str:
    """Extract all text from a PDF using pdfplumber."""
    import pdfplumber
    pages = []
    with pdfplumber.open(uploaded_file) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text:
                pages.append(f"[Page {i}]\n{text.strip()}")
    return "\n\n".join(pages)


def text_to_speech(text: str) -> bytes:
    """Convert text to MP3 bytes using gTTS."""
    from gtts import gTTS
    buf = io.BytesIO()
    gTTS(text=text, lang="en", slow=False).write_to_fp(buf)
    buf.seek(0)
    return buf.read()


def transcribe_audio(audio_bytes: bytes, api_key: str) -> str:
    """Transcribe audio with Groq Whisper API."""
    from groq import Groq
    client = Groq(api_key=api_key)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=f,
                response_format="text",
            )
        return result.strip()
    finally:
        os.unlink(tmp_path)


def autoplay_audio(audio_bytes: bytes):
    """Embed and autoplay audio in the page."""
    b64 = base64.b64encode(audio_bytes).decode()
    st.markdown(
        f'<audio autoplay controls style="width:100%;margin-top:8px;">'
        f'<source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>',
        unsafe_allow_html=True,
    )


# ── Session state ─────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "messages":       [],
        "bot":            None,
        "api_key_set":    False,
        "api_key_value":  "",
        "system_prompt":  DEFAULT_SYSTEM_PROMPT,
        "selected_model": list(AVAILABLE_MODELS.keys())[0],
        "pdf_context":    None,
        "pdf_name":       None,
        "voice_out":      False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="chat-header"><h1>🎓 CampusMind AI</h1></div>',
                unsafe_allow_html=True)

    # API Key
    st.markdown('<div class="sidebar-section">API Key</div>', unsafe_allow_html=True)
    env_key, secret_key = os.environ.get("GROQ_API_KEY", ""), ""
    try:
        secret_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        pass

    api_key_input = st.text_input(
        "Groq API Key", value=env_key or secret_key,
        type="password", placeholder="gsk_...",
        label_visibility="collapsed",
    )

    if api_key_input:
        if not st.session_state.api_key_set or st.session_state.bot is None:
            try:
                st.session_state.bot = Chatbot(
                    api_key=api_key_input,
                    system_prompt=st.session_state.system_prompt,
                    model=st.session_state.selected_model,
                )
                st.session_state.api_key_set  = True
                st.session_state.api_key_value = api_key_input
            except Exception as e:
                st.error(f"Failed to init: {e}")
        st.success("✓ Connected", icon="⚡")
    else:
        st.info("Free key at [console.groq.com](https://console.groq.com)")

    # Model
    st.markdown('<div class="sidebar-section">Model</div>', unsafe_allow_html=True)
    model_label = st.selectbox("Model", list(AVAILABLE_MODELS.values()),
                               index=0, label_visibility="collapsed")
    sel_model_id = [k for k, v in AVAILABLE_MODELS.items() if v == model_label][0]
    if st.session_state.bot and sel_model_id != st.session_state.selected_model:
        st.session_state.selected_model = sel_model_id
        st.session_state.bot.change_model(sel_model_id)

    # Persona
    st.markdown('<div class="sidebar-section">Persona</div>', unsafe_allow_html=True)
    new_prompt = st.text_area("System prompt", value=st.session_state.system_prompt,
                              height=90, label_visibility="collapsed")
    if new_prompt != st.session_state.system_prompt:
        st.session_state.system_prompt = new_prompt
        if st.session_state.bot:
            st.session_state.bot.change_system_prompt(new_prompt)

    personas = {
        "🤖 Default":       DEFAULT_SYSTEM_PROMPT,
        "🐍 Python Tutor":  "You are an expert Python tutor. Give code examples with every answer.",
        "✍️ Writing Coach": "You are a professional writing coach. Be encouraging but direct.",
        "📊 Data Analyst":  "You are a data analyst. Help with data, SQL, and visualization.",
        "🏴‍☠️ Pirate":       "You are a swashbuckling pirate. Answer in pirate speak. Arrr!",
    }
    for lbl, pmt in personas.items():
        if st.button(lbl, key=f"p_{lbl}"):
            st.session_state.system_prompt = pmt
            if st.session_state.bot:
                st.session_state.bot.change_system_prompt(pmt)
            st.rerun()

    # Voice settings
    st.markdown('<div class="sidebar-section">🎙 Voice Settings</div>', unsafe_allow_html=True)
    st.session_state.voice_out = st.toggle(
        "🔊 Speak AI replies aloud", value=st.session_state.voice_out)

    # Controls
    st.markdown('<div class="sidebar-section">Controls</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑 Clear"):
            st.session_state.messages   = []
            st.session_state.pdf_context = None
            st.session_state.pdf_name   = None
            if st.session_state.bot:
                st.session_state.bot.reset()
            st.rerun()
    with c2:
        if st.button("💾 Export") and st.session_state.messages:
            st.download_button(
                "⬇ JSON", json.dumps(st.session_state.messages, indent=2),
                "campusmind_chat.json", "application/json",
            )

    if st.session_state.messages:
        turns = len(st.session_state.messages) // 2
        words = sum(len(m["content"].split()) for m in st.session_state.messages)
        st.markdown(
            f'<div class="stats-row">'
            f'<div class="stat-chip">turns <span>{turns}</span></div>'
            f'<div class="stat-chip">words <span>{words}</span></div>'
            f'</div>', unsafe_allow_html=True,
        )


# ── Main header ───────────────────────────────────────────────────────────────
st.markdown(
    '<div class="chat-header">'
    '<h1>CampusMind AI</h1>'
    '<span class="badge">Free & Fast</span>'
    '</div>',
    unsafe_allow_html=True,
)

tab_chat, tab_pdf, tab_voice = st.tabs(["💬 Chat", "📄 PDF Upload", "🎙 Voice"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CHAT
# ══════════════════════════════════════════════════════════════════════════════
with tab_chat:

    if st.session_state.pdf_name:
        st.markdown(
            f'<div class="pdf-banner">📄 <b>{st.session_state.pdf_name}</b> loaded '
            f'— your next question will be answered using this document.</div>',
            unsafe_allow_html=True,
        )
    if st.session_state.voice_out:
        st.markdown(
            '<div class="voice-banner">🔊 Voice output ON — replies will be read aloud.</div>',
            unsafe_allow_html=True,
        )

    # Message history
    if not st.session_state.messages:
        st.markdown("""
        <div class="empty-state">
            <div class="big-icon">🎓</div>
            <h3>Welcome to CampusMind AI</h3>
            <p>Type below · upload a PDF · or use your voice.<br>
            Add your Groq API key in the sidebar to begin.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            is_user = msg["role"] == "user"
            st.markdown(
                f'<div class="message-row {"user" if is_user else "bot"}">'
                f'<div class="avatar {"user-av" if is_user else "bot-av"}">{"U" if is_user else "🎓"}</div>'
                f'<div class="bubble {"user-bubble" if is_user else "bot-bubble"}">{msg["content"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Chat input
    if prompt := st.chat_input("Message CampusMind AI...",
                               disabled=not st.session_state.api_key_set):
        if not st.session_state.bot:
            st.error("Enter your API key in the sidebar first.")
        else:
            # Inject PDF context if a PDF is loaded
            full_prompt = prompt
            if st.session_state.pdf_context:
                full_prompt = (
                    "The user uploaded a PDF. Use it to answer their question.\n\n"
                    f"=== PDF CONTENT ===\n{st.session_state.pdf_context}\n=== END PDF ===\n\n"
                    f"User question: {prompt}"
                )
                st.session_state.pdf_context = None   # inject once only

            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner("Thinking..."):
                reply = st.session_state.bot.chat(full_prompt)
            st.session_state.messages.append({"role": "assistant", "content": reply})

            if st.session_state.voice_out:
                try:
                    autoplay_audio(text_to_speech(reply))
                except Exception as e:
                    st.warning(f"Voice output failed: {e}")

            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PDF UPLOAD
# ══════════════════════════════════════════════════════════════════════════════
with tab_pdf:
    st.markdown("### 📄 Chat with a PDF")
    st.markdown(
        "Upload lecture notes, research papers, or any PDF. "
        "CampusMind AI will read it and answer your questions in the **Chat** tab."
    )

    uploaded_pdf = st.file_uploader("Choose a PDF", type=["pdf"])

    if uploaded_pdf:
        with st.spinner(f"Reading **{uploaded_pdf.name}**..."):
            try:
                pdf_text = extract_pdf_text(uploaded_pdf)
                if not pdf_text.strip():
                    st.error("No text found. The PDF may be a scanned image — try a text-based PDF.")
                else:
                    st.session_state.pdf_context = pdf_text
                    st.session_state.pdf_name    = uploaded_pdf.name
                    if st.session_state.bot:
                        st.session_state.bot.reset()
                    st.session_state.messages = []

                    st.success(f"✅ **{uploaded_pdf.name}** loaded!")
                    c1, c2 = st.columns(2)
                    c1.metric("Words", f"{len(pdf_text.split()):,}")
                    c2.metric("Characters", f"{len(pdf_text):,}")

                    with st.expander("👁 Preview first 1000 characters"):
                        st.text(pdf_text[:1000] + ("..." if len(pdf_text) > 1000 else ""))

                    st.info("Now switch to the **💬 Chat** tab and ask anything about this document!")

            except Exception as e:
                st.error(f"Could not read PDF: {e}")
                st.markdown("**Tips:** PDF must not be password-protected and must contain selectable text.")

    elif st.session_state.pdf_name:
        st.info(f"📄 Loaded: **{st.session_state.pdf_name}**")
        if st.button("🗑 Remove PDF"):
            st.session_state.pdf_context = None
            st.session_state.pdf_name    = None
            st.rerun()
    else:
        st.markdown("""
        <div class="empty-state" style="padding:40px 20px;">
            <div class="big-icon">📄</div>
            <h3>No PDF loaded</h3>
            <p>Upload a PDF above to start chatting with your document.</p>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — VOICE
# ══════════════════════════════════════════════════════════════════════════════
with tab_voice:
    st.markdown("### 🎙 Voice Chat")
    st.markdown(
        "**How it works:** Record → Groq Whisper transcribes → AI replies → gTTS speaks the answer."
    )

    if not st.session_state.api_key_set:
        st.warning("⚠️ Enter your Groq API key in the sidebar first.")
    else:
        # ── Voice recorder ───────────────────────────────────────────────────
        try:
            from audio_recorder_streamlit import audio_recorder

            st.markdown("#### 🎤 Step 1 — Click the mic and speak")
            audio_bytes = audio_recorder(
                text="Click to record",
                recording_color="#f97316",
                neutral_color="#6b7280",
                icon_name="microphone",
                icon_size="2x",
                pause_threshold=3.0,
                sample_rate=16000,
            )

            if audio_bytes:
                st.audio(audio_bytes, format="audio/wav")

                st.markdown("#### 📝 Step 2 — Transcribing with Groq Whisper")
                with st.spinner("Transcribing your voice..."):
                    try:
                        transcript = transcribe_audio(
                            audio_bytes, st.session_state.api_key_value
                        )
                        st.success(f"**You said:** {transcript}")

                        st.markdown("#### 🤖 Step 3 — Getting AI reply")
                        with st.spinner("CampusMind AI is thinking..."):
                            reply = st.session_state.bot.chat(transcript)

                        st.session_state.messages.append({"role": "user",      "content": f"🎙 {transcript}"})
                        st.session_state.messages.append({"role": "assistant", "content": reply})

                        st.markdown(f"**🎓 CampusMind AI:** {reply}")

                        st.markdown("#### 🔊 Step 4 — Playing reply")
                        with st.spinner("Generating speech..."):
                            autoplay_audio(text_to_speech(reply))

                    except Exception as e:
                        st.error(f"Error: {e}")
                        st.info("Tip: Allow microphone access in your browser settings.")

        except ImportError:
            st.error("Package `audio-recorder-streamlit` is missing.")
            st.code("pip install audio-recorder-streamlit", language="bash")
            st.info("Install the package and restart the app.")

        # ── Text-to-speech tester ────────────────────────────────────────────
        st.divider()
        st.markdown("#### 🔊 Or type text and hear it spoken")
        tts_input = st.text_area("Type anything", placeholder="Hello! I am CampusMind AI.", height=90)
        if st.button("▶ Speak this text"):
            if tts_input.strip():
                with st.spinner("Generating audio..."):
                    try:
                        autoplay_audio(text_to_speech(tts_input))
                    except Exception as e:
                        st.error(f"TTS error: {e}")
            else:
                st.warning("Type some text first.")
