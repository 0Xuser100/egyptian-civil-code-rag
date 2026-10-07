import json
from pathlib import Path

import faiss

from rag.config import CHUNKS_PATH, INDEX_PATH, TOP_K
from rag.embeddings import load_embedding_model
from rag.generator import generate_answer
from rag.retriever import retrieve_articles


def build_context(results: list[dict]) -> str:
    context_parts = []

    for result in results:
        context_parts.append(
            f"""
Article {result["article_number"]}

Arabic:
{result["text_ar"]}

English:
{result["text_en"]}
""".strip()
        )

    return "\n\n---\n\n".join(context_parts)


class RAGPipeline:
    def __init__(self) -> None:
        self.embedding_model = load_embedding_model()
        self.index = faiss.read_index(str(INDEX_PATH))

        with Path(CHUNKS_PATH).open("r", encoding="utf-8") as file:
            self.chunks = json.load(file)

    def ask(self, question: str) -> dict:
        results = retrieve_articles(
            question=question,
            model=self.embedding_model,
            index=self.index,
            chunks=self.chunks,
            top_k=TOP_K,
        )

        context = build_context(results)

        answer = generate_answer(
            question=question,
            context=context,
        )

        return {
            "question": question,
            "answer": answer,
            "sources": [
                {
                    "article_number": result["article_number"],
                    "score": result["score"],
                    "id": result["id"],
                }
                for result in results
            ],
        }