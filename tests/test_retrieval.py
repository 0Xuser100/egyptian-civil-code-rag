import json
from pathlib import Path

import faiss

from rag.config import CHUNKS_PATH, INDEX_PATH
from rag.embeddings import load_embedding_model
from rag.retriever import retrieve_articles


def test_retrieval_returns_expected_article() -> None:
    model = load_embedding_model()
    index = faiss.read_index(str(INDEX_PATH))

    with Path(CHUNKS_PATH).open("r", encoding="utf-8") as file:
        chunks = json.load(file)

    results = retrieve_articles(
        question="ما هو سن الرشد؟",
        model=model,
        index=index,
        chunks=chunks,
        top_k=5,
    )

    assert len(results) == 5
    assert results[0]["article_number"] == 44