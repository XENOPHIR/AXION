import os
from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

KNOWLEDGE_BASE_PATH = "knowledge_base/accessbank_faq.txt"


class RAGEngine:
    """Simple TF-IDF based RAG engine for AccessBank knowledge base."""

    def __init__(self):
        self.chunks = []
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.vectors = None
        self._load_and_index()

    def _load_and_index(self):
        """Load the knowledge base and build TF-IDF index."""
        with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        # Split into chunks by section (## headers)
        raw_chunks = content.split("\n## ")
        self.chunks = []
        for chunk in raw_chunks:
            chunk = chunk.strip()
            if chunk:
                # Clean up and keep meaningful chunks
                lines = chunk.split("\n")
                if len(lines) >= 2:
                    self.chunks.append(chunk)

        # Build TF-IDF matrix
        self.vectors = self.vectorizer.fit_transform(self.chunks)
        print(f"[RAG] Indexed {len(self.chunks)} knowledge base sections.")

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """Retrieve the most relevant chunks for a query."""
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.vectors).flatten()
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if similarities[idx] > 0.01:  # Minimum relevance threshold
                results.append(self.chunks[idx])

        return results

    def get_context(self, query: str) -> str:
        """Get formatted context string for LLM prompt."""
        chunks = self.retrieve(query, top_k=3)
        if not chunks:
            return "No specific information found in the knowledge base."
        return "\n\n---\n\n".join(chunks)


# Singleton instance
_rag_engine = None


def get_rag_engine() -> RAGEngine:
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine
