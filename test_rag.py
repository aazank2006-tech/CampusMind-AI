"""
test_rag.py — tests for the RAG pipeline (rag.py + its integration in chatbot.py).

Run from the project folder:
    pip install pytest reportlab          # test-only extras (reportlab builds a sample PDF)
    pytest -v test_rag.py

By default the embedding model is replaced by a tiny deterministic stand-in
(hashed bag-of-words), so the tests run offline, in a second, and exercise
everything *around* the model: chunking, FAISS indexing/search, replace/append,
prompt injection, failure handling and the PDF extraction step from app.py.

To also check *semantic* retrieval with the real model (downloads ~70 MB once):
    RUN_REAL_EMBEDDINGS=1 pytest -v -k real_model test_rag.py
"""

import ast
import hashlib
import io
import os
import re
import types

import numpy as np
import pytest

import chatbot
import rag
from rag import RAGStore, chunk_text, CHUNK_TOKENS, CHARS_PER_TOKEN


# ── Test doubles ─────────────────────────────────────────────────────────────
class StubEmbedder:
    """Deterministic hashed bag-of-words embedder (lexical, not semantic)."""
    DIM = 512

    def _vec(self, text):
        v = np.zeros(self.DIM, dtype="float32")
        for w in re.findall(r"[a-z0-9+]+", text.lower()):
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % self.DIM] += 1.0
        return v

    def _norm(self, m):
        n = np.linalg.norm(m, axis=1, keepdims=True)
        n[n == 0] = 1
        return (m / n).astype("float32")

    def embed_passages(self, texts):
        return self._norm(np.array([self._vec(t) for t in texts]))

    def embed_query(self, text):
        return self._norm(np.array([self._vec(text)]))


class FakeGroq:
    """Stands in for groq.Groq; records every request so tests can inspect the prompt."""
    calls = []

    def __init__(self, api_key=None):
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self._create))

    def _create(self, **kw):
        FakeGroq.calls.append(kw)
        msg = types.SimpleNamespace(content="ok")
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    """Use the stub embedder and fake Groq unless a test opts out."""
    stub = StubEmbedder()
    monkeypatch.setattr(rag, "get_embedder", lambda: stub)
    monkeypatch.setattr(chatbot, "Groq", FakeGroq)
    FakeGroq.calls.clear()


def make_bot():
    return chatbot.Chatbot(api_key="test-key")        # no user_id → no Firestore


def system_prompt_of(call):
    return call["messages"][0]["content"]


# ── A long, multi-topic "lecture" ───────────────────────────────────────────
TOPICS = {
    "photosynthesis": "Photosynthesis converts light energy into chemical energy inside chloroplasts. "
                      "Chlorophyll absorbs sunlight, and the Calvin cycle fixes carbon dioxide into glucose. ",
    "static":         "A static local variable in C++ keeps its value between function calls. "
                      "It is initialised once and lives for the whole program, unlike an automatic variable. ",
    "recursion":      "Recursion solves a problem by calling the same function on a smaller input until a base case stops it. ",
    "osmosis":        "Osmosis is the diffusion of water across a semi-permeable membrane toward higher solute concentration. ",
    "compilers":      "A compiler translates source code into machine code through lexing, parsing and code generation. ",
}


def long_document(repeat=12):
    """Each topic gets its own several-paragraph section, so topics land in different chunks."""
    filler = "This paragraph continues the lecture with more worked examples and exercises for students. "
    sections = []
    for name, sentence in TOPICS.items():
        paras = [sentence * 3 + filler * 6 for _ in range(repeat // 3)]
        sections.append("\n\n".join(paras))
    return "\n\n".join(sections)


# ═════════════════════════════ chunking ═════════════════════════════════════
def test_chunks_respect_size_limit_and_are_not_empty():
    chunks = chunk_text(long_document())
    assert len(chunks) > 3
    assert all(c.strip() for c in chunks)
    assert max(len(c) for c in chunks) <= CHUNK_TOKENS * CHARS_PER_TOKEN


def test_chunks_overlap_and_cover_all_text():
    text = long_document()
    chunks = chunk_text(text, chunk_tokens=128, overlap_tokens=24)
    # coverage: every word of the source appears in some chunk
    covered = set(" ".join(chunks).split())
    assert set(text.split()) <= covered
    # overlap: consecutive chunks share some trailing/leading words
    shared = [bool(set(a.split()[-15:]) & set(b.split()[:25])) for a, b in zip(chunks, chunks[1:])]
    assert all(shared)


def test_chunking_handles_no_whitespace_and_empty_input():
    blob = "x" * 10_000                                     # nothing to split on → hard cut
    assert all(len(c) <= 128 * CHARS_PER_TOKEN for c in chunk_text(blob, chunk_tokens=128))
    assert chunk_text("") == [] and chunk_text("   \n\n  ") == []
    assert chunk_text("tiny doc") == ["tiny doc"]


# ═════════════════════════ store: retrieval ═════════════════════════════════
def test_search_returns_the_relevant_chunk():
    store = RAGStore()
    n = store.add_document("lecture.pdf", long_document())
    assert n == store.chunk_count > 3
    hits = store.search("what is a static local variable in C++?", k=3)
    assert hits and "static local variable" in hits[0].text
    assert hits[0].source == "lecture.pdf"
    assert hits == sorted(hits, key=lambda h: -h.score)


def test_search_on_empty_store_or_blank_query():
    store = RAGStore()
    assert store.is_empty and store.search("anything") == []
    store.add_document("a.pdf", "some text about osmosis")
    assert store.search("   ") == []


def test_min_score_filters_weak_matches():
    store = RAGStore()
    store.add_document("a.pdf", long_document())
    assert store.search("zzzz qqqq", k=4, min_score=0.9) == []


# ═════════════════════ store: multiple documents ════════════════════════════
def test_append_keeps_both_documents_searchable():
    store = RAGStore()
    store.add_document("bio.pdf", TOPICS["photosynthesis"] * 5)
    store.add_document("cpp.pdf", TOPICS["static"] * 5)             # replace_all=False → append
    assert sorted(store.sources) == ["bio.pdf", "cpp.pdf"]
    assert store.search("chlorophyll sunlight")[0].source == "bio.pdf"
    assert store.search("static variable function calls")[0].source == "cpp.pdf"


def test_replace_all_drops_the_previous_document():
    store = RAGStore()
    store.add_document("bio.pdf", TOPICS["photosynthesis"] * 5)
    store.add_document("cpp.pdf", TOPICS["static"] * 5, replace_all=True)
    assert store.sources == ["cpp.pdf"]
    assert all(h.source == "cpp.pdf" for h in store.search("chlorophyll sunlight"))


def test_same_name_replaces_only_itself():
    store = RAGStore()
    store.add_document("a.pdf", "old text about osmosis " * 20)
    store.add_document("b.pdf", TOPICS["static"] * 5)
    store.add_document("a.pdf", "new text about recursion " * 20)
    assert sorted(store.sources) == ["a.pdf", "b.pdf"]
    texts = " ".join(h.text for h in store.search("osmosis recursion static", k=10))
    assert "old text" not in texts and "new text" in texts


def test_failed_embedding_leaves_existing_index_intact():
    store = RAGStore()
    store.add_document("good.pdf", TOPICS["static"] * 5)
    before = store.chunk_count

    class Boom(StubEmbedder):
        def embed_passages(self, texts):
            raise RuntimeError("model download failed")

    store._embedder = Boom()
    with pytest.raises(RuntimeError):
        store.add_document("bad.pdf", "whatever " * 50, replace_all=True)
    assert store.sources == ["good.pdf"] and store.chunk_count == before


def test_clear_empties_the_store():
    store = RAGStore()
    store.add_document("a.pdf", "text " * 100)
    store.clear()
    assert store.is_empty and store.chunk_count == 0 and store.search("text") == []


# ═════════════════════════ chatbot integration ══════════════════════════════
def test_no_pdf_means_plain_chat_with_no_document_block():
    bot = make_bot()
    assert bot.chat("hello there") == "ok"
    assert "DOCUMENT" not in system_prompt_of(FakeGroq.calls[-1])
    assert bot.rag is None                                  # RAG machinery never created


def test_chat_injects_retrieved_excerpts_not_the_whole_pdf():
    bot = make_bot()
    doc = long_document(repeat=30)
    assert len(doc) > 6000
    assert bot.setup_rag("lecture.pdf", doc) > 3
    bot.chat("Explain what a static local variable in C++ does")
    sp = system_prompt_of(FakeGroq.calls[-1])
    assert "--- DOCUMENT EXCERPTS ---" in sp and "[Excerpt 1]" in sp
    assert "static local variable" in sp
    assert sp.count("[Excerpt ") <= rag.TOP_K
    assert "photosynthesis" not in sp.lower().split("--- document excerpts ---")[1]   # unrelated topic left out
    assert len(sp) < len(doc)                               # far smaller than pasting everything
    assert "lecture.pdf" not in sp                          # file name never leaks to the model (privacy rules)


def test_privacy_rules_and_base_prompt_are_preserved():
    bot = make_bot()
    bot.setup_rag("a.pdf", long_document())
    bot.chat("What is osmosis and how does it work?")
    sp = system_prompt_of(FakeGroq.calls[-1])
    assert sp.startswith(chatbot.BASE_SYSTEM_PROMPT)
    assert "NEVER mention, reveal, or repeat any person's name" in sp
    assert "NEVER refer to who wrote or created the document" in sp


def test_persona_and_memory_still_work_alongside_rag():
    bot = make_bot()
    bot.set_persona("🐍 Python Tutor", "You are a Python tutor.")
    bot.chat("my name is Aazan")
    bot.setup_rag("a.pdf", long_document())
    bot.chat("What does recursion need to stop?")
    sp = system_prompt_of(FakeGroq.calls[-1])
    assert sp.startswith("You are a Python tutor.")
    assert "Name: Aazan" in sp and "--- DOCUMENT EXCERPTS ---" in sp
    assert FakeGroq.calls[-1]["max_tokens"] == chatbot.DEFAULT_MAX_TOKENS == 1024


def test_history_is_still_capped_at_20_turns():
    bot = make_bot()
    bot.setup_rag("a.pdf", long_document())
    for i in range(30):
        bot.chat(f"question number {i} about compilers and parsing")
    assert len(bot.history.messages) <= chatbot.MAX_HISTORY_TURNS * 2 + 1


def test_short_followup_borrows_previous_question_for_retrieval():
    bot = make_bot()
    bot.setup_rag("a.pdf", long_document())
    bot.chat("How does a compiler turn source code into machine code?")
    bot.chat("explain more")                                 # no searchable content by itself
    assert "compiler translates source code" in system_prompt_of(FakeGroq.calls[-1])


def test_clear_rag_returns_to_plain_chat():
    bot = make_bot()
    bot.setup_rag("a.pdf", long_document())
    bot.clear_rag()
    bot.chat("what is osmosis?")
    assert "DOCUMENT" not in system_prompt_of(FakeGroq.calls[-1])


def test_second_pdf_replaces_first_by_default_and_appends_on_request():
    bot = make_bot()
    bot.setup_rag("bio.pdf", TOPICS["photosynthesis"] * 5)
    bot.setup_rag("cpp.pdf", TOPICS["static"] * 5)                       # default: replace
    assert bot.rag.sources == ["cpp.pdf"]
    bot.setup_rag("bio.pdf", TOPICS["photosynthesis"] * 5, replace=False)  # append
    assert sorted(bot.rag.sources) == ["bio.pdf", "cpp.pdf"]


def test_setup_failure_returns_zero_and_chat_still_works(monkeypatch):
    class Boom:
        def embed_passages(self, texts): raise RuntimeError("no model")
        def embed_query(self, text):     raise RuntimeError("no model")

    monkeypatch.setattr(rag, "get_embedder", lambda: Boom())
    bot = make_bot()
    assert bot.setup_rag("a.pdf", long_document()) == 0
    assert bot.chat("hello") == "ok"
    assert "DOCUMENT" not in system_prompt_of(FakeGroq.calls[-1])


def test_retrieval_failure_falls_back_to_plain_chat():
    bot = make_bot()
    bot.setup_rag("a.pdf", long_document())

    class Boom(StubEmbedder):
        def embed_query(self, text): raise RuntimeError("boom")

    bot.rag._embedder = Boom()
    assert bot.chat("what is osmosis in biology class?") == "ok"
    assert "DOCUMENT" not in system_prompt_of(FakeGroq.calls[-1])


def test_old_api_names_still_work():
    bot = make_bot()
    bot.set_pdf_context(long_document())
    bot.chat("what is a static local variable in C++?")
    assert "[Excerpt 1]" in system_prompt_of(FakeGroq.calls[-1])
    bot.clear_pdf_context()
    assert bot.rag.is_empty


def test_answer_beyond_the_old_6000_char_cutoff_is_now_found():
    """The old code could only ever see doc[:6000]. A fact deep in the PDF is now retrievable."""
    filler = "General course administration notes and reminders about deadlines. " * 200
    secret = "The grading policy states that the final project is worth 35 percent of the course mark."
    doc = filler + "\n\n" + secret + "\n\n" + filler
    assert secret not in doc[:6000]                          # old approach: invisible
    bot = make_bot()
    bot.setup_rag("syllabus.pdf", doc)
    bot.chat("How much is the final project worth in the grading policy?")
    assert "35 percent" in system_prompt_of(FakeGroq.calls[-1])


# ═══════════════════ real upload flow: PDF → app.py's extractor → RAG ═══════
def _load_extract_pdf_text():
    """Pull the real extract_pdf_text() out of app.py without running the Streamlit UI."""
    src = open(os.path.join(os.path.dirname(__file__), "app.py"), encoding="utf-8").read()
    fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "extract_pdf_text")
    ns = {"st": types.SimpleNamespace(error=lambda *a, **k: None)}
    exec(compile(ast.Module([fn], []), "app.py", "exec"), ns)
    return ns["extract_pdf_text"]


def _make_pdf(pages):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    for lines in pages:
        y = 800
        for line in lines:
            c.drawString(50, y, line)
            y -= 16
        c.showPage()
    c.save()
    buf.seek(0)
    return buf


def test_full_upload_flow_with_a_real_pdf():
    pytest.importorskip("reportlab")
    pytest.importorskip("pdfplumber")
    extract = _load_extract_pdf_text()

    pages = []
    for i in range(30):                                      # 30 pages ≈ well over 6,000 chars
        lines = [f"Lecture {i}: general discussion and worked examples for this week."] * 40
        pages.append(lines)
    pages[24] = ["Lecture 24: Static and automatic variables"] + [
        "A static local variable is initialised only once and keeps its value between calls.",
        "An automatic variable is created on each call and destroyed when the function returns.",
    ] * 3 + pages[24]

    text = extract(_make_pdf(pages))                         # exactly what app.py does on upload
    assert len(text) > 6000
    old_context = text[:6000]
    assert "static local variable" not in old_context.lower()   # old pipeline could not answer this

    bot = make_bot()
    assert bot.setup_rag("lecture.pdf", text, replace=True) > 3
    bot.chat("When is a static local variable initialised?")
    assert "static local variable" in system_prompt_of(FakeGroq.calls[-1]).lower()


# ═══════════════════ optional: real embedding model (semantic check) ════════
@pytest.mark.skipif(not os.environ.get("RUN_REAL_EMBEDDINGS"), reason="set RUN_REAL_EMBEDDINGS=1 (downloads ~70 MB)")
def test_real_model_retrieves_by_meaning_not_keywords(monkeypatch):
    monkeypatch.undo()                                       # drop the stub; use fastembed for real
    store = RAGStore()
    store.add_document("lecture.pdf", long_document())
    # no shared keywords with the photosynthesis passage
    hits = store.search("how do plants turn sunlight into food?", k=2)
    assert any("Photosynthesis" in h.text or "chloroplast" in h.text for h in hits)
