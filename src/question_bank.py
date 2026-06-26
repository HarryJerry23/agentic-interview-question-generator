"""Question Bank — TF-IDF searchable index over pre-prepared JSON question files.

Loads interview_questions.json + scraped_questions.json into a single searchable
corpus. Uses TF-IDF cosine similarity for ranked retrieval.

No SQLite, no live scraping — all data comes from data/ JSON files.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.models import QuestionDetail


class QuestionBankRetriever:
    """TF-IDF search over the pre-indexed question bank."""

    def __init__(self, questions: list[dict]):
        self._corpus = questions
        self._vectorizer: TfidfVectorizer | None = None
        self._tfidf_matrix = None
        self._build_index()

    def _build_index(self):
        """Build TF-IDF index over all question content."""
        if not self._corpus:
            return

        texts = [q.get("content", "") for q in self._corpus]
        self._vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=10000,
            ngram_range=(1, 2),
        )
        self._tfidf_matrix = self._vectorizer.fit_transform(texts)

    def search(
        self,
        query: str,
        difficulty: str | None = None,
        source: str | None = None,
        limit: int = 10,
        exclude_ids: set[str] | None = None,
    ) -> list[QuestionDetail]:
        """Search by TF-IDF cosine similarity with optional filters."""
        if not self._corpus or self._tfidf_matrix is None:
            return []

        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._tfidf_matrix).flatten()

        candidates = []
        for i, row in enumerate(self._corpus):
            q_id = row.get("id", "")
            if exclude_ids and q_id in exclude_ids:
                continue
            if difficulty and row.get("difficulty") and row["difficulty"] != difficulty:
                continue
            if source and row.get("source") and row["source"] != source:
                continue
            if scores[i] < 0.01:
                continue
            candidates.append((scores[i], row))

        candidates.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, row in candidates[:limit]:
            results.append(QuestionDetail(
                question_id=row.get("id", ""),
                category=row.get("category", row.get("question_type", "GENERAL")),
                content=row.get("content", ""),
                topic=row.get("topic", ""),
                sub_topic=row.get("sub_topic"),
                difficulty=row.get("difficulty", "Medium"),
                asked_in_company=row.get("company"),
                role=row.get("role"),
                source_url=row.get("source_url"),
                source="interview_db",
            ))

        return results

    def get_stats(self) -> dict:
        """Get question bank statistics."""
        if not self._corpus:
            return {"total": 0}

        sources = {}
        difficulties = {}
        for q in self._corpus:
            s = "interview_db"
            sources[s] = sources.get(s, 0) + 1
            d = q.get("difficulty", "Medium")
            difficulties[d] = difficulties.get(d, 0) + 1

        return {
            "total": len(self._corpus),
            "by_source": sources,
            "by_difficulty": difficulties,
        }


# ── Singleton ───────────────────────────────────────────────────────────────

_retriever: QuestionBankRetriever | None = None


def get_retriever() -> QuestionBankRetriever:
    """Get or create the question bank retriever (loads from DataStore)."""
    global _retriever
    if _retriever is None:
        from src.data_loader import get_data_store
        data_store = get_data_store()
        all_questions = data_store.get_all_questions()
        _retriever = QuestionBankRetriever(all_questions)
        print(f"Question bank ready: {len(all_questions)} questions indexed for TF-IDF search")
    return _retriever
