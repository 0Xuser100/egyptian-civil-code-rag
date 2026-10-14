from sentence_transformers import SentenceTransformer

from rag.config import EMBEDDING_MODEL


def load_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(
        EMBEDDING_MODEL,
        device="cpu",
    )
