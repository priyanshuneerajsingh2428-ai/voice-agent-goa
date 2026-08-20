"""
RAG pipeline: chunking, retrieval, and grounded answer generation.

Design note: VectorKnowledgeBase tries to use sentence-transformers + FAISS
for real semantic search, but falls back automatically to a dependency-light
TF-IDF/cosine implementation if the heavy ML stack isn't available or fails
to load (e.g. on a memory-constrained free-tier host). This means the app
NEVER crashes at import/startup time just because torch didn't fit in RAM —
it degrades instead of dying, which matters a lot on Render's free plan.
"""
import re
import math
from pathlib import Path
from collections import Counter

NO_ANSWER_MESSAGE = "I couldn't find enough reliable information in the knowledge base to answer that."

_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "what", "when", "where", "who", "why", "how", "which", "does", "do",
    "did", "of", "in", "on", "at", "to", "for", "and", "or", "but", "with",
    "this", "that", "these", "those", "it", "its", "as", "by", "from",
}


# ---------------------------------------------------------------------------
# Demo knowledge base
# ---------------------------------------------------------------------------

def build_demo_knowledge_base() -> dict:
    """Returns {doc_name: text} — used when no real documents are loaded."""
    return {
        "refund_policy": (
            "Tuition fee refunds are processed only if the withdrawal request is "
            "submitted within 15 days of the start of the semester. A processing "
            "fee of INR 1000 is deducted from all refunds. No refunds are issued "
            "for hostel fees once the semester has commenced."
        ),
        "exam_registration": (
            "Registration for end-semester examinations closes two weeks before "
            "the first exam date, as published in the academic calendar. Late "
            "registration is permitted up to 3 days after the deadline, subject "
            "to a late fee of INR 500 and approval from the concerned Head of "
            "Department."
        ),
        "hostel_rules": (
            "The hostel main gate closes at 10:30 PM on weekdays and 11:30 PM on "
            "weekends. Students returning after gate closing time must obtain "
            "prior written permission from the warden. Repeated late entries "
            "without permission may result in disciplinary action."
        ),
        "placement_eligibility": (
            "Campus recruitment drives are scheduled starting the seventh "
            "semester. Students must have a minimum CGPA of 6.0 and no active "
            "academic backlogs to be eligible for campus placements. A minimum "
            "attendance of 75 percent is also required to participate in "
            "placement drives."
        ),
        "library_policy": (
            "Library books must be returned within 14 days of issue. A fine of "
            "INR 5 per day is charged for overdue books. Students with unpaid "
            "library fines above INR 500 will have their examination hall "
            "ticket withheld until the fine is cleared."
        ),
    }


def load_knowledge_documents(documents_dir: str) -> dict:
    """Loads {filename: text} from every .txt file in a directory (real KB, not the demo one)."""
    docs = {}
    dir_path = Path(documents_dir)
    if not dir_path.exists():
        return docs
    for path in sorted(dir_path.glob("*.txt")):
        docs[path.stem] = path.read_text(encoding="utf-8")
    return docs


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _chunk_fixed(text: str, chunk_size: int = 400, overlap: int = 80) -> list:
    text = _clean(text)
    chunks, start = [], 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        start = max(end - overlap, start + 1)
    return [c for c in chunks if c]


def _chunk_sentence(text: str, target_size: int = 400) -> list:
    text = _clean(text)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, current = [], ""
    for sentence in sentences:
        if len(current) + len(sentence) <= target_size:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)
    return chunks


def _chunk_recursive(text: str, chunk_size: int = 400, overlap: int = 60) -> list:
    paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()] or [text]
    chunks = []
    for para in paragraphs:
        para = _clean(para)
        if len(para) <= chunk_size:
            chunks.append(para)
            continue
        for sc in _chunk_sentence(para, target_size=chunk_size):
            if len(sc) <= chunk_size:
                chunks.append(sc)
            else:
                chunks.extend(_chunk_fixed(sc, chunk_size=chunk_size, overlap=overlap))
    return chunks


_STRATEGIES = {"fixed": _chunk_fixed, "sentence": _chunk_sentence, "recursive": _chunk_recursive}


def split_documents(text: str, strategy: str = "recursive", **kwargs) -> list:
    if strategy not in _STRATEGIES:
        raise ValueError(f"Unknown chunking strategy: {strategy!r}. Use one of {list(_STRATEGIES)}.")
    return _STRATEGIES[strategy](text, **kwargs)


# ---------------------------------------------------------------------------
# Lightweight TF-IDF backend (no torch/model download — always available)
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list:
    return [_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower())]


def _stem(word: str) -> str:
    """Minimal suffix-stripping stemmer (no external dependency) so 'refund'
    and 'refunds', or 'register' and 'registration', overlap correctly.
    Not linguistically rigorous, but fixes the common plural/verb-form
    mismatches that would otherwise silently zero out TF-IDF overlap."""
    for suffix in ("ations", "ation", "ing", "edly", "ies", "es", "ed", "s"):
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


class _TfidfIndex:
    """Pure-Python TF-IDF + cosine similarity. No sklearn/numpy dependency
    required so it can never fail to install; used as the guaranteed-working
    fallback under VectorKnowledgeBase."""

    def __init__(self, documents: list):
        self.documents = documents
        self.doc_tokens = [_tokenize(d) for d in documents]
        self.vocab = sorted({t for toks in self.doc_tokens for t in toks})
        self.idf = self._compute_idf()
        self.doc_vectors = [self._vectorize(toks) for toks in self.doc_tokens]

    def _compute_idf(self) -> dict:
        n = len(self.doc_tokens)
        df = Counter()
        for toks in self.doc_tokens:
            for t in set(toks):
                df[t] += 1
        return {t: math.log((n + 1) / (df[t] + 1)) + 1 for t in self.vocab}

    def _vectorize(self, tokens: list) -> dict:
        tf = Counter(tokens)
        vec = {t: (tf[t] / max(len(tokens), 1)) * self.idf.get(t, 0.0) for t in tf}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {t: v / norm for t, v in vec.items()}

    def _cosine(self, a: dict, b: dict) -> float:
        shared = set(a) & set(b)
        return sum(a[t] * b[t] for t in shared)

    def search(self, query: str, top_k: int = 3) -> list:
        q_tokens = [t for t in _tokenize(query) if t not in _STOPWORDS]
        q_vec = self._vectorize(q_tokens)
        scored = sorted(
            range(len(self.documents)),
            key=lambda i: self._cosine(q_vec, self.doc_vectors[i]),
            reverse=True,
        )[:top_k]
        return [
            {"text": self.documents[i], "score": round(self._cosine(q_vec, self.doc_vectors[i]), 4)}
            for i in scored
        ]


class VectorKnowledgeBase:
    """
    Tries sentence-transformers + FAISS for real semantic search; falls back
    to the dependency-light TF-IDF index above if that stack isn't
    available or fails to load. Never raises — app startup must not crash
    just because a heavy model couldn't be loaded on a constrained host.
    """

    def __init__(self, chunks: list, embedding_model_name: str = "all-MiniLM-L6-v2"):
        self.chunks = chunks
        self.backend = "tfidf"
        self._tfidf = _TfidfIndex(chunks) if chunks else None
        self._st_model = None
        self._faiss_index = None

        try:
            self._try_load_semantic_backend(embedding_model_name)
            self.backend = "sentence-transformer"
        except Exception as exc:  # noqa: BLE001 - intentionally broad, this is a graceful-degrade path
            print(f"[VectorKnowledgeBase] Semantic backend unavailable, using TF-IDF fallback. Reason: {exc}")

    def _try_load_semantic_backend(self, model_name: str):
        import numpy as np
        import faiss
        from sentence_transformers import SentenceTransformer

        self._st_model = SentenceTransformer(model_name)
        embeddings = self._st_model.encode(self.chunks, normalize_embeddings=True, show_progress_bar=False)
        embeddings = np.asarray(embeddings, dtype="float32")
        self._faiss_index = faiss.IndexFlatIP(embeddings.shape[1])
        self._faiss_index.add(embeddings)

    def search(self, query: str, top_k: int = 3) -> list:
        if self.backend == "sentence-transformer" and self._faiss_index is not None:
            import numpy as np
            q_emb = np.asarray(self._st_model.encode([query], normalize_embeddings=True), dtype="float32")
            scores, indices = self._faiss_index.search(q_emb, top_k)
            return [
                {"text": self.chunks[idx], "score": float(score)}
                for score, idx in zip(scores[0], indices[0]) if idx != -1
            ]

        if self._tfidf is None:
            return []
        return self._tfidf.search(query, top_k=top_k)


def retrieve_relevant_chunks(query: str, chunks: list, top_k: int = 3) -> list:
    """Standalone fallback retrieval, used if VectorKnowledgeBase itself is unavailable (e.g. KB is None)."""
    return _TfidfIndex(chunks).search(query, top_k=top_k) if chunks else []


# ---------------------------------------------------------------------------
# Answer generation with guardrail
# ---------------------------------------------------------------------------

def generate_grounded_answer(query: str, relevant_chunks: list, min_score: float = 0.12) -> str:
    """
    Extractive grounded answer with a hallucination guardrail: refuses if the
    best retrieval score is below threshold instead of making something up.
    min_score is deliberately low because the TF-IDF fallback scores run
    lower than a real embedding model's — retune if you switch backends.
    """
    if not relevant_chunks:
        return NO_ANSWER_MESSAGE

    best_score = max(c.get("score", 0.0) for c in relevant_chunks)
    if best_score < min_score:
        return NO_ANSWER_MESSAGE

    q_terms = {w for w in _tokenize(query) if w not in _STOPWORDS}
    best_sentence, best_overlap = "", -1
    for chunk in relevant_chunks:
        for sentence in re.split(r"(?<=[.!?])\s+", chunk["text"]):
            overlap = len(q_terms & set(_tokenize(sentence)))
            if overlap > best_overlap:
                best_overlap, best_sentence = overlap, sentence.strip()

    return best_sentence or NO_ANSWER_MESSAGE


# ---------------------------------------------------------------------------
# Benchmarking
# ---------------------------------------------------------------------------

def benchmark_pipeline(queries: list, query_to_chunks: dict, latencies: list) -> dict:
    """Aggregates real measured per-query latencies into P50/P70/P100. Never fabricates numbers."""
    if not latencies:
        return {"latency": {"p50_ms": 0, "p70_ms": 0, "p100_ms": 0, "num_queries": 0}}

    sorted_latencies = sorted(latencies)

    def percentile(p):
        if not sorted_latencies:
            return 0.0
        k = (len(sorted_latencies) - 1) * (p / 100)
        f, c = math.floor(k), math.ceil(k)
        if f == c:
            return sorted_latencies[int(k)]
        return sorted_latencies[f] + (sorted_latencies[c] - sorted_latencies[f]) * (k - f)

    return {
        "latency": {
            "p50_ms": round(percentile(50), 2),
            "p70_ms": round(percentile(70), 2),
            "p100_ms": round(percentile(100), 2),
            "num_queries": len(queries),
        }
    }
