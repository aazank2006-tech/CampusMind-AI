"""
rag.py — Retrieval-Augmented Generation (RAG) pipeline for CampusMind AI.

Replaces "paste the first 6,000 characters of the PDF into the system prompt"
with a real retrieval pipeline:

    PDF text ──► chunk_text() ──► embedder ──► FAISS index ──► search(query) ──► top-K chunks

1. CHUNKING  (chunk_text)
   Recursive splitting: try to break on paragraph boundaries ("\\n\\n") first,
   then lines, then sentences (". "), then words, and only hard-cut as a last
   resort. Pieces are then packed greedily into chunks of ~CHUNK_TOKENS tokens,
   and each new chunk starts with the last ~CHUNK_OVERLAP_TOKENS tokens of the
   previous one, so a sentence or definition that straddles a boundary is still
   fully present in at least one chunk.

   Token counts are *estimated* at CHARS_PER_TOKEN (4) characters per token —
   a standard rule of thumb for English prose. That avoids shipping a tokenizer
   just for sizing. Note the embedding model below accepts at most 512 word-
   pieces: for very token-dense text (source code, formulas) a chunk can exceed
   that, in which case only its first ~512 tokens influence the chunk's
   *embedding*. The LLM still receives the full chunk text.

2. EMBEDDINGS  (FastEmbedEmbedder)
   `BAAI/bge-small-en-v1.5` (384-dim) run through `fastembed`, which uses ONNX
   Runtime instead of PyTorch. That keeps the install small (~100 MB instead of
   ~2 GB) and fast on CPU — important on Streamlit Community Cloud. The model
   (~70 MB) is downloaded on first use and shared by every session in the
   server process (it is stateless, so sharing it is safe — unlike per-user
   state such as the persona, which lives on each Chatbot instance).
   Vectors are L2-normalised, so inner product == cosine similarity.

3. VECTOR STORE  (RAGStore)
   An in-memory FAISS `IndexFlatIP` (exact search; for the few hundred/thousand
   chunks of a lecture PDF this is instant and needs no external server).
   One RAGStore lives on each Chatbot, i.e. per Streamlit session, so users
   never see each other's documents. It is *not* written to Firestore: like
   the old pdf_context, it lasts for the session and is rebuilt by re-uploading.

4. RETRIEVAL  (RAGStore.search)
   Embed the user's query with the same model, return the TOP_K most similar
   chunks with their cosine scores. Chunks are tagged with their source file so
   several PDFs can live in one index (see RAGStore.add_document).
"""

from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass
from typing import Optional, Protocol

import faiss
import numpy as np

logger = logging.getLogger(__name__)

# ── Tunables ────────────────────────────────────────────────────────────────
EMBEDDING_MODEL      = "BAAI/bge-small-en-v1.5"
CHUNK_TOKENS         = 512     # target chunk size (estimated tokens)
CHUNK_OVERLAP_TOKENS = 64      # tail of previous chunk repeated at the start of the next
CHARS_PER_TOKEN      = 4       # rough English average; see module docstring
TOP_K                = 4       # chunks injected per question (~2k tokens at defaults)

_SEPARATORS = ["\n\n", "\n", ". ", " "]   # coarse → fine split points


# ══════════════════════════════════════════════════════════════
# 1. CHUNKING
# ══════════════════════════════════════════════════════════════
def _normalize(text: str) -> str:
    """Collapse runs of spaces/tabs and 3+ newlines (common in pdfplumber output)."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_recursive(text: str, limit: int, separators: list[str]) -> list[str]:
    """
    Split `text` into pieces of at most `limit` characters, preferring the
    coarsest separator that works. The separator stays attached to the end of
    each piece, so concatenating pieces reproduces the original text.
    """
    if len(text) <= limit:
        return [text]
    if not separators:  # no natural boundary left — hard cut
        return [text[i:i + limit] for i in range(0, len(text), limit)]

    sep, finer = separators[0], separators[1:]
    parts = text.split(sep)
    pieces: list[str] = []
    for i, part in enumerate(parts):
        piece = part + (sep if i < len(parts) - 1 else "")
        if not piece:
            continue
        if len(piece) <= limit:
            pieces.append(piece)
        else:
            pieces.extend(_split_recursive(piece, limit, finer))
    return pieces


def _overlap_tail(text: str, n_chars: int) -> str:
    """Last ~n_chars of `text`, trimmed forward to a word boundary."""
    if n_chars <= 0 or len(text) <= n_chars:
        return ""  # a chunk shorter than the overlap would just be duplicated
    tail = text[-n_chars:]
    m = re.search(r"\s", tail)
    return tail[m.end():] if m else tail


def chunk_text(
    text: str,
    chunk_tokens: int = CHUNK_TOKENS,
    overlap_tokens: int = CHUNK_OVERLAP_TOKENS,
) -> list[str]:
    """
    Split `text` into overlapping chunks of roughly `chunk_tokens` tokens.

    Strategy: recursive boundary-aware splitting (paragraph → line → sentence →
    word), greedy packing up to the size limit, and `overlap_tokens` of trailing
    context carried into the next chunk. No chunk exceeds
    chunk_tokens * CHARS_PER_TOKEN characters. Returns [] for empty input.
    """
    text = _normalize(text or "")
    if not text:
        return []

    max_chars = max(chunk_tokens * CHARS_PER_TOKEN, 64)
    overlap_chars = min(overlap_tokens * CHARS_PER_TOKEN, max_chars // 2)
    # Pieces are capped so that (overlap tail + piece) always fits in one chunk.
    pieces = _split_recursive(text, max_chars - overlap_chars, _SEPARATORS)

    chunks: list[str] = []
    cur = ""
    for piece in pieces:
        if cur and len(cur) + len(piece) > max_chars:
            chunks.append(cur.strip())
            cur = _overlap_tail(cur, overlap_chars) + piece
        else:
            cur += piece
    if cur.strip():
        chunks.append(cur.strip())
    return [c for c in chunks if c]


# ══════════════════════════════════════════════════════════════
# 2. EMBEDDINGS
# ══════════════════════════════════════════════════════════════
class Embedder(Protocol):
    """Anything that maps text to L2-normalised float32 vectors (shape: [n, dim])."""

    def embed_passages(self, texts: list[str]) -> np.ndarray: ...
    def embed_query(self, text: str) -> np.ndarray: ...


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    matrix = np.asarray(matrix, dtype="float32")
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


class FastEmbedEmbedder:
    """
    Sentence embeddings via `fastembed` (ONNX Runtime, no PyTorch).

    BGE v1.5 models work without the optional "Represent this sentence…" query
    prefix, so queries and passages go through the same path.
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        from fastembed import TextEmbedding  # imported lazily: heavy, and only needed once a PDF is uploaded
        logger.info("Loading embedding model %s (first run downloads ~70 MB)…", model_name)
        self._model = TextEmbedding(model_name=model_name)

    def embed_passages(self, texts: list[str]) -> np.ndarray:
        return _l2_normalize(np.array(list(self._model.passage_embed(texts))))

    def embed_query(self, text: str) -> np.ndarray:
        return _l2_normalize(np.array(list(self._model.query_embed(text))))


_embedder: Optional[Embedder] = None
_embedder_lock = threading.Lock()


def get_embedder() -> Embedder:
    """Process-wide embedder, created on first use (model load takes a few seconds)."""
    global _embedder
    with _embedder_lock:
        if _embedder is None:
            _embedder = FastEmbedEmbedder()
        return _embedder


# ══════════════════════════════════════════════════════════════
# 3 + 4. VECTOR STORE AND RETRIEVAL
# ══════════════════════════════════════════════════════════════
@dataclass
class RetrievedChunk:
    text: str
    source: str        # file name the chunk came from
    chunk_index: int   # position of the chunk within that file
    score: float       # cosine similarity to the query (higher = closer)


class RAGStore:
    """
    Per-session vector store over one or more documents.

    Multiple-PDF policy
    -------------------
    * `add_document(name, text)`                    → APPEND: keeps other documents;
      a document re-added under the same `name` replaces its own earlier chunks.
    * `add_document(name, text, replace_all=True)`  → REPLACE: the index afterwards
      contains only this document.
    Embedding happens *before* anything is modified, so a failure (e.g. the model
    can't be downloaded) leaves the existing index untouched.

    FAISS flat indexes can't cheaply delete one document's vectors, so the index
    is rebuilt from the stored per-document vectors after every change — trivial
    at this scale (hundreds of 384-dim vectors).
    """

    def __init__(
        self,
        embedder: Optional[Embedder] = None,
        chunk_tokens: int = CHUNK_TOKENS,
        overlap_tokens: int = CHUNK_OVERLAP_TOKENS,
    ):
        self._embedder = embedder            # None → resolved lazily via get_embedder()
        self.chunk_tokens = chunk_tokens
        self.overlap_tokens = overlap_tokens
        self._docs: dict[str, tuple[list[str], np.ndarray]] = {}   # name → (chunks, vectors)
        self._index: Optional[faiss.Index] = None
        self._entries: list[tuple[str, int, str]] = []             # row i of index → (source, chunk_idx, text)

    # ── properties ──────────────────────────────────────────────
    @property
    def embedder(self) -> Embedder:
        if self._embedder is None:
            self._embedder = get_embedder()
        return self._embedder

    @property
    def is_empty(self) -> bool:
        return self._index is None

    @property
    def chunk_count(self) -> int:
        return len(self._entries)

    @property
    def sources(self) -> list[str]:
        return list(self._docs)

    # ── indexing ────────────────────────────────────────────────
    def add_document(self, name: str, text: str, replace_all: bool = False) -> int:
        """Chunk, embed and index `text`. Returns the number of chunks (0 = nothing indexable)."""
        chunks = chunk_text(text, self.chunk_tokens, self.overlap_tokens)
        if not chunks:
            return 0
        vectors = self.embedder.embed_passages(chunks)   # may raise — nothing mutated yet
        if replace_all:
            self._docs.clear()
        self._docs[name] = (chunks, vectors)
        self._rebuild()
        logger.info("RAG: indexed %s — %d chunks (store now holds %d chunks from %d document(s))",
                    name, len(chunks), self.chunk_count, len(self._docs))
        return len(chunks)

    def clear(self):
        self._docs.clear()
        self._rebuild()

    def _rebuild(self):
        if not self._docs:
            self._index, self._entries = None, []
            return
        entries: list[tuple[str, int, str]] = []
        mats: list[np.ndarray] = []
        for source, (chunks, vecs) in self._docs.items():
            entries.extend((source, i, c) for i, c in enumerate(chunks))
            mats.append(vecs)
        matrix = np.ascontiguousarray(np.vstack(mats), dtype="float32")
        index = faiss.IndexFlatIP(matrix.shape[1])   # inner product on unit vectors = cosine
        index.add(matrix)
        self._index, self._entries = index, entries

    # ── retrieval ───────────────────────────────────────────────
    def search(self, query: str, k: int = TOP_K, min_score: Optional[float] = None) -> list[RetrievedChunk]:
        """
        Return up to `k` chunks most similar to `query`, best first.
        `min_score` optionally drops weak matches; it is off by default because
        useful cut-offs depend on the embedding model and need tuning on real data.
        """
        if self._index is None or not query or not query.strip():
            return []
        q = self.embedder.embed_query(query)
        scores, ids = self._index.search(q, min(k, self._index.ntotal))
        hits: list[RetrievedChunk] = []
        for score, idx in zip(scores[0], ids[0]):
            if idx < 0 or (min_score is not None and score < min_score):
                continue
            source, chunk_index, text = self._entries[idx]
            hits.append(RetrievedChunk(text=text, source=source, chunk_index=int(chunk_index), score=float(score)))
        return hits
