import json
from pathlib import Path

import faiss
import numpy as np
import ollama
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL = "BAAI/bge-m3"
LLM_MODEL = "qwen2.5:3b"

INDEX_PATH = Path("data/processed/civil_code.faiss")
CHUNKS_PATH = Path("data/processed/rag_chunks.json")

TOP_K = 5


def retrieve_articles(
    question: str,
    model: SentenceTransformer,
    index: faiss.Index,
    chunks: list[dict],
) -> list[dict]:
    query_embedding = model.encode(
        [question],
        normalize_embeddings=True,
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype="float32",
    )

    scores, indices = index.search(
        query_embedding,
        TOP_K,
    )

    results = []

    for score, idx in zip(scores[0], indices[0]):
        chunk = chunks[idx]

        results.append(
            {
                "score": float(score),
                "article_number": chunk["article_number"],
                "id": chunk["id"],
                "text_ar": chunk["text_ar"],
                "text_en": chunk["text_en"],
            }
        )

    return results


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


def ask_llm(question: str, context: str) -> str:
    system_prompt = """
You are a legal RAG assistant for the Egyptian Civil Code.

Answer the user's question using ONLY the provided context.

Rules:
- Do not use outside knowledge.
- Do not invent legal information.
- If the context does not contain enough information, say that the answer
  cannot be determined from the provided articles.
- Always mention the relevant article number when the answer is supported
  by the context.
- Answer clearly and concisely.
"""

    user_prompt = f"""
Context:
{context}

Question:
{question}
"""
    print("\n===== CONTEXT SENT TO LLM =====")
    print(context)
    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )

    return response["message"]["content"]


def main() -> None:
    print("Loading embedding model...")
    embedding_model = SentenceTransformer(
        EMBEDDING_MODEL,
        device="cpu",
    )

    print("Loading FAISS index...")
    index = faiss.read_index(str(INDEX_PATH))

    with CHUNKS_PATH.open("r", encoding="utf-8") as file:
        chunks = json.load(file)

    question = "ما هو سن الرشد؟"

    print(f"\nQuestion: {question}")

    results = retrieve_articles(
        question,
        embedding_model,
        index,
        chunks,
    )

    print("\n===== RETRIEVED ARTICLES =====")

    for rank, result in enumerate(results, start=1):
        print(
            f"{rank}. Article {result['article_number']} "
            f"(score={result['score']:.4f})"
        )

    context = build_context(results)

    print("\n===== ASKING QWEN2.5 =====")

    answer = ask_llm(
        question,
        context,
    )

    print("\n===== FINAL ANSWER =====")
    print(answer)


if __name__ == "__main__":
    main()