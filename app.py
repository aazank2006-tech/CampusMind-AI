"""
app.py — CampusMind AI — Streamlit UI
Run: streamlit run app.py
"""

import os, json, io, uuid
import streamlit as st
from chatbot import Chatbot, AVAILABLE_MODELS, BASE_SYSTEM_PROMPT

st.set_page_config(
    page_title="CampusMind AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme toggle (☀️ Light / 🌙 Dark) ───────────────────────────────────────
st.sidebar.markdown("## 🎓 CampusMind AI")
st.sidebar.markdown("---")
is_light_mode = st.sidebar.toggle("☀️ Light Mode", value=False, key="is_light_mode")
st.sidebar.markdown("")

DARK_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;700;800&display=swap');

:root, body { color-scheme: dark; }

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
/* Theme toggle label + track — brand orange instead of Streamlit's default red */
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    color: #e2e8f0 !important;
    text-transform: none !important;
    font-weight: 600 !important;
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
/* Active persona (Streamlit "primary" button type) */
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: #f97316 !important;
    border-color: #f97316 !important;
    color: #0f1117 !important;
    font-weight: 700 !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
    background: #fb923c !important;
    border-color: #fb923c !important;
    color: #0f1117 !important;
}

/* Sidebar section dividers */
.sidebar-divider {
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    color: #475569 !important;
    margin: 14px 0 8px !important;
    padding-bottom: 5px !important;
    border-bottom: 1px solid #2d3148 !important;
}

/* ── Main area ── */
.main-header {
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    padding: 8px 0 16px !important;
    border-bottom: 1px solid #2d3148 !important;
    margin-bottom: 20px !important;
}
.main-header h1 {
    font-size: 1.6rem !important;
    font-weight: 800 !important;
    color: #f1f5f9 !important;
    margin: 0 !important;
    font-family: 'Syne', sans-serif !important;
    letter-spacing: -0.5px !important;
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
    background: #1e3a5f !important;
    border: 1px solid #2563eb !important;
    color: #e2e8f0 !important;
    padding: 12px 16px;
    border-radius: 16px 16px 4px 16px;
    max-width: 70%;
    font-size: 0.9rem;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
}
.bubble-bot {
    background: #1a1d27 !important;
    border: 1px solid #2d3148 !important;
    color: #e2e8f0 !important;
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
.av-user { background: #f97316 !important; color: #000 !important; }
.av-bot  { background: #2d3148 !important; color: #e2e8f0 !important; }

/* Native st.chat_message — used for the assistant's replies. Streamlit
   sets its own text color here based on its (OS-following) theme, which
   is why replies could look washed-out/invisible against our forced
   background — these overrides make it match this theme regardless. */
[data-testid="stChatMessage"] {
    background-color: transparent !important;
}
[data-testid="stChatMessageAvatarAssistant"] {
    background-color: #2d3148 !important;
}
[data-testid="stChatMessageContent"],
[data-testid="stChatMessageContent"] p,
[data-testid="stChatMessageContent"] li,
[data-testid="stChatMessageContent"] span,
[data-testid="stChatMessageContent"] strong,
[data-testid="stChatMessageContent"] em {
    color: #e2e8f0 !important;
}
[data-testid="stChatMessageContent"] a {
    color: #f97316 !important;
}
[data-testid="stChatMessageContent"] code {
    background-color: #0f1117 !important;
    color: #f97316 !important;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #475569 !important;
}
.empty-state h2 { color: #94a3b8 !important; font-size: 1.6rem; margin-bottom: 8px; font-family: 'Syne', sans-serif; font-weight: 700; letter-spacing: -0.5px; line-height: 1.3; }
.empty-state p  { color: #475569 !important; font-size: 0.85rem; line-height: 1.7; }

/* ── PDF banner ── */
.pdf-banner {
    background: #0f2027 !important;
    border: 1px solid #1e40af !important;
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 0.82rem;
    color: #93c5fd !important;
    margin-bottom: 16px;
}

/* ── Persona banner ── */
.persona-banner {
    background: #1f1508 !important;
    border: 1px solid #92400e !important;
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 0.82rem;
    color: #fdba74 !important;
    margin-bottom: 16px;
}

/* ── Session banner ── */
.session-box {
    background: #0f1117 !important;
    border: 1px solid #2d3148 !important;
    border-radius: 8px;
    padding: 8px 10px;
    font-size: 0.72rem;
    color: #64748b !important;
    word-break: break-all;
    margin-bottom: 8px;
}

/* ── Chips ── */
.chip-row { display: flex; gap: 8px; flex-wrap: wrap; margin: 8px 0; }
.chip {
    background: #0f1117 !important; border: 1px solid #2d3148 !important;
    border-radius: 20px; padding: 3px 10px;
    font-size: 0.7rem; color: #64748b !important;
}
.chip span { color: #f97316 !important; font-weight: 600; }

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

/* ── Force dark mode on native Streamlit chrome ──────────────────────────── */
/* Top header bar (behind Share/star/edit icons on Streamlit Cloud) */
header[data-testid="stHeader"] {
    background-color: #0f1117 !important;
}
/* Thin gradient "decoration" bar Streamlit shows at the very top */
div[data-testid="stDecoration"] {
    background-image: none !important;
    background-color: #0f1117 !important;
}
[data-testid="stToolbar"] {
    background-color: transparent !important;
    color: #e2e8f0 !important;
}
[data-testid="stToolbar"] svg {
    fill: #94a3b8 !important;
}

/* Fixed bottom bar that wraps the chat input — not a descendant of .stApp,
   so it needs its own override or it falls back to the browser/OS theme */
[data-testid="stBottom"],
[data-testid="stBottomBlockContainer"] {
    background-color: #0f1117 !important;
}

/* File uploader — untouched by earlier CSS, so it rendered in Streamlit's
   default light widget style */
[data-testid="stFileUploader"] section,
[data-testid="stFileUploaderDropzone"] {
    background-color: #0f1117 !important;
    border: 1px dashed #2d3148 !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] * {
    color: #64748b !important;
    fill: #64748b !important;
}
[data-testid="stFileUploader"] button {
    background-color: #1a1d27 !important;
    color: #e2e8f0 !important;
    border: 1px solid #2d3148 !important;
    border-radius: 6px !important;
}
[data-testid="stFileUploaderFile"] {
    background-color: #1a1d27 !important;
    color: #e2e8f0 !important;
}

/* Selectbox / dropdown popovers render outside .stApp, so they need
   their own override to avoid a white flash when opened */
div[data-baseweb="popover"],
div[data-baseweb="menu"],
ul[role="listbox"] {
    background-color: #1a1d27 !important;
    border: 1px solid #2d3148 !important;
}
ul[role="listbox"] li,
div[data-baseweb="menu"] li {
    background-color: #1a1d27 !important;
    color: #e2e8f0 !important;
}
ul[role="listbox"] li:hover {
    background-color: #0f1117 !important;
    color: #f97316 !important;
}

</style>
"""

LIGHT_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;700;800&display=swap');

:root, body { color-scheme: light; }

body, .stApp {
    background-color: #ffffff !important;
    color: #1e293b !important;
    font-family: 'DM Mono', monospace !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background-color: #f8fafc !important;
    border-right: 1px solid #e2e8f0 !important;
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
    color: #64748b !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}
/* Theme toggle label + track — brand orange instead of Streamlit's default red */
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    color: #1e293b !important;
    text-transform: none !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea {
    background-color: #ffffff !important;
    color: #1e293b !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background-color: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    color: #1e293b !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
}
section[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    color: #475569 !important;
    border-radius: 8px !important;
    font-size: 0.8rem !important;
    padding: 0.35rem 0.7rem !important;
    margin-bottom: 4px !important;
    transition: all 0.2s !important;
    text-align: left !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    border-color: #ea580c !important;
    color: #ea580c !important;
}
/* Active persona (Streamlit "primary" button type) */
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: #f97316 !important;
    border-color: #f97316 !important;
    color: #1e293b !important;
    font-weight: 700 !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
    background: #fb923c !important;
    border-color: #fb923c !important;
    color: #1e293b !important;
}

/* Sidebar section dividers */
.sidebar-divider {
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    color: #334155 !important;
    margin: 14px 0 8px !important;
    padding-bottom: 5px !important;
    border-bottom: 1px solid #e2e8f0 !important;
}

/* ── Main area ── */
.main-header {
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    padding: 8px 0 16px !important;
    border-bottom: 1px solid #e2e8f0 !important;
    margin-bottom: 20px !important;
}
.main-header h1 {
    font-size: 1.6rem !important;
    font-weight: 800 !important;
    color: #0f172a !important;
    margin: 0 !important;
    font-family: 'Syne', sans-serif !important;
    letter-spacing: -0.5px !important;
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
    background: #eff6ff !important;
    border: 1px solid #2563eb !important;
    color: #1e3a5f !important;
    padding: 12px 16px;
    border-radius: 16px 16px 4px 16px;
    max-width: 70%;
    font-size: 0.9rem;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
}
.bubble-bot {
    background: #f1f5f9 !important;
    border: 1px solid #e2e8f0 !important;
    color: #1e293b !important;
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
.av-user { background: #f97316 !important; color: #000 !important; }
.av-bot  { background: #e2e8f0 !important; color: #334155 !important; }

/* Native st.chat_message — used for the assistant's replies. Streamlit
   sets its own text color here based on its (OS-following) theme, which
   is why replies could look washed-out/invisible against our forced
   background — these overrides make it match this theme regardless. */
[data-testid="stChatMessage"] {
    background-color: transparent !important;
}
[data-testid="stChatMessageAvatarAssistant"] {
    background-color: #e2e8f0 !important;
}
[data-testid="stChatMessageContent"],
[data-testid="stChatMessageContent"] p,
[data-testid="stChatMessageContent"] li,
[data-testid="stChatMessageContent"] span,
[data-testid="stChatMessageContent"] strong,
[data-testid="stChatMessageContent"] em {
    color: #1e293b !important;
}
[data-testid="stChatMessageContent"] a {
    color: #ea580c !important;
}
[data-testid="stChatMessageContent"] code {
    background-color: #f1f5f9 !important;
    color: #c2410c !important;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #475569 !important;
}
.empty-state h2 { color: #334155 !important; font-size: 1.6rem; margin-bottom: 8px; font-family: 'Syne', sans-serif; font-weight: 700; letter-spacing: -0.5px; line-height: 1.3; }
.empty-state p  { color: #475569 !important; font-size: 0.85rem; line-height: 1.7; }

/* ── PDF banner ── */
.pdf-banner {
    background: #eff6ff !important;
    border: 1px solid #93c5fd !important;
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 0.82rem;
    color: #1d4ed8 !important;
    margin-bottom: 16px;
}

/* ── Persona banner ── */
.persona-banner {
    background: #fff7ed !important;
    border: 1px solid #fdba74 !important;
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 0.82rem;
    color: #c2410c !important;
    margin-bottom: 16px;
}

/* ── Session banner ── */
.session-box {
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px;
    padding: 8px 10px;
    font-size: 0.72rem;
    color: #475569 !important;
    word-break: break-all;
    margin-bottom: 8px;
}

/* ── Chips ── */
.chip-row { display: flex; gap: 8px; flex-wrap: wrap; margin: 8px 0; }
.chip {
    background: #f1f5f9 !important; border: 1px solid #e2e8f0 !important;
    border-radius: 20px; padding: 3px 10px;
    font-size: 0.7rem; color: #475569 !important;
}
.chip span { color: #c2410c !important; font-weight: 600; }

/* ── Chat input ── */
[data-testid="stChatInput"] {
    max-width: 720px !important;
    margin: 0 auto !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}
[data-testid="stChatInput"] > div {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 10px !important;
    padding: 1px 8px !important;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06) !important;
}
[data-testid="stChatInputTextArea"] {
    color: #1e293b !important;
    font-size: 0.88rem !important;
    min-height: 28px !important;
    max-height: 90px !important;
    padding-top: 6px !important;
    padding-bottom: 6px !important;
}
[data-testid="stChatInput"] button {
    background: #ea580c !important;
    border-radius: 8px !important;
}

footer { visibility: hidden; }

/* ── Force light mode on native Streamlit chrome ─────────────────────────── */
/* Top header bar (behind Share/star/edit icons on Streamlit Cloud) */
header[data-testid="stHeader"] {
    background-color: #ffffff !important;
}
/* Thin gradient "decoration" bar Streamlit shows at the very top */
div[data-testid="stDecoration"] {
    background-image: none !important;
    background-color: #ffffff !important;
}
[data-testid="stToolbar"] {
    background-color: transparent !important;
    color: #1e293b !important;
}
[data-testid="stToolbar"] svg {
    fill: #475569 !important;
}

/* Fixed bottom bar that wraps the chat input — not a descendant of .stApp,
   so it needs its own override or it falls back to the browser/OS theme
   (this was the black strip behind the chat box) */
[data-testid="stBottom"],
[data-testid="stBottomBlockContainer"] {
    background-color: #ffffff !important;
}

/* File uploader */
[data-testid="stFileUploader"] section,
[data-testid="stFileUploaderDropzone"] {
    background-color: #f8fafc !important;
    border: 1px dashed #cbd5e1 !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] * {
    color: #475569 !important;
    fill: #475569 !important;
}
[data-testid="stFileUploader"] button {
    background-color: #ffffff !important;
    color: #1e293b !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 6px !important;
}
[data-testid="stFileUploaderFile"] {
    background-color: #f1f5f9 !important;
    color: #1e293b !important;
}

/* Selectbox / dropdown popovers render outside .stApp, so they need
   their own override to stay consistent with the light theme when opened */
div[data-baseweb="popover"],
div[data-baseweb="menu"],
ul[role="listbox"] {
    background-color: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
}
ul[role="listbox"] li,
div[data-baseweb="menu"] li {
    background-color: #ffffff !important;
    color: #1e293b !important;
}
ul[role="listbox"] li:hover {
    background-color: #f1f5f9 !important;
    color: #ea580c !important;
}

</style>
"""

st.markdown(LIGHT_THEME_CSS if is_light_mode else DARK_THEME_CSS, unsafe_allow_html=True)



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

def get_or_create_session_id() -> str:
    """
    Reads a `uid` query param from the URL, or generates one and writes it
    back so the URL becomes a durable link the user can bookmark/save to
    return to the same Firestore-backed memory and chat history later.
    """
    qp = st.query_params
    if "uid" in qp and qp["uid"]:
        return qp["uid"]
    new_id = uuid.uuid4().hex[:12]
    st.query_params["uid"] = new_id
    return new_id


# ── Persona definitions ─────────────────────────────────────────────────────
PERSONAS = {
    "🎓 Campus Assistant": BASE_SYSTEM_PROMPT,
    "🐍 Python Tutor":     "You are CampusMind AI acting as a Python tutor. Only answer coding questions. Give short code examples.",
    "✍️ Writing Coach":    "You are CampusMind AI acting as a writing coach. Help with clarity, grammar, and style.",
    "📊 Study Planner":    "You are CampusMind AI acting as a study planner. Help with schedules, time management, and exam prep.",
    "🌍 Research Helper":  "You are CampusMind AI acting as a research assistant. Help find sources, summarize topics, and structure essays.",
}


# ── Session state ─────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "messages":         [],
        "bot":              None,
        "api_key_set":      False,
        "selected_model":   list(AVAILABLE_MODELS.keys())[0],
        "pdf_loaded":       False,
        "pdf_name":         "",
        "tts_audio":        None,
        "current_persona":  "🎓 Campus Assistant",
        "session_id":       None,
        "history_restored": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

if st.session_state.session_id is None:
    st.session_state.session_id = get_or_create_session_id()


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
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
                    user_id=st.session_state.session_id,   # ← enables Firestore persistence
                )
                st.session_state.api_key_set = True

                # Pull any previously saved chat into the UI on first load
                if not st.session_state.history_restored:
                    st.session_state.messages = list(st.session_state.bot.history.messages)
                    st.session_state.history_restored = True
            except Exception as e:
                st.error(f"Bot init failed: {e}")
        st.success("✅ CampusMind AI is ready!")
    else:
        st.error(
            "⚠️ API key not set.\n\n"
            "**Local:** `export GROQ_API_KEY=gsk_...`\n\n"
            "**Cloud:** Settings → Secrets → `GROQ_API_KEY = \"gsk_...\"`"
        )

    # ── Session / persistence ────────────────────────────────
    st.markdown('<div class="sidebar-divider">🔗 Session</div>', unsafe_allow_html=True)
    if st.session_state.bot and st.session_state.bot.store and st.session_state.bot.store.available:
        st.caption("Memory & chat persist to Firestore. Bookmark this page's URL to return to them later.")
    else:
        st.caption("Firestore not configured — memory/chat will reset on restart. See README.")
    st.markdown(f'<div class="session-box">ID: {st.session_state.session_id}</div>', unsafe_allow_html=True)

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
            st.session_state.bot.clear_memory()
            st.rerun()

    # ── Personas ──────────────────────────────────────────────
    # NOTE: persona choice is stored on `st.session_state.bot` (an instance
    # attribute), NOT a module-level global. A shared global would leak one
    # user's persona into every other session sharing the same server process.
    st.markdown('<div class="sidebar-divider">🎭 Personas</div>', unsafe_allow_html=True)
    for label, prompt in PERSONAS.items():
        is_active = st.session_state.current_persona == label
        if st.button(
            label,
            key=f"persona_btn_{label}",
            type="primary" if is_active else "secondary",
        ):
            if st.session_state.bot:
                st.session_state.bot.set_persona(label, prompt)
                st.session_state.current_persona = label
                st.toast(f"Switched to {label}", icon="🎭")
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

# Persona banner (only show when a non-default persona is active)
if st.session_state.current_persona != "🎓 Campus Assistant":
    st.markdown(
        f'<div class="persona-banner">🎭 <strong>{st.session_state.current_persona}</strong>'
        f' mode is active</div>',
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
            # Use st.chat_message so markdown + code blocks render with syntax highlighting
            with st.chat_message("assistant", avatar="🎓"):
                st.markdown(msg["content"])

# ── Chat input ────────────────────────────────────────────────────────────────
prompt = st.chat_input(
    "Message CampusMind AI…",
    disabled=not st.session_state.api_key_set,
)

if prompt and st.session_state.bot:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("CampusMind AI is thinking..."):
        reply = st.session_state.bot.chat(prompt)   # also persists to Firestore internally
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

# ── Auto-scroll to bottom after every response ────────────────
st.markdown("""
<script>
    const scrollToBottom = () => {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    };
    // Run immediately and after a short delay to catch late-rendering elements
    scrollToBottom();
    setTimeout(scrollToBottom, 300);
    setTimeout(scrollToBottom, 800);
</script>
""", unsafe_allow_html=True)
