import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-m3"

INDEX_PATH = Path("data/processed/civil_code.faiss")
CHUNKS_PATH = Path("data/processed/rag_chunks.json")

TOP_K = 5


def main() -> None:
    print("Loading model...")
    model = SentenceTransformer(MODEL_NAME, device="cpu")

    print("Loading FAISS index...")
    index = faiss.read_index(str(INDEX_PATH))

    with CHUNKS_PATH.open("r", encoding="utf-8") as file:
        chunks = json.load(file)

    question = "ما هو سن الرشد؟"

    print(f"\nQuestion: {question}")
    print("Searching...\n")

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

    print("===== TOP RESULTS =====")

    for rank, (score, idx) in enumerate(
        zip(scores[0], indices[0]),
        start=1,
    ):
        chunk = chunks[idx]

        print(f"\n--- Result {rank} ---")
        print(f"Score: {score:.4f}")
        print(f"Article: {chunk['article_number']}")
        print(f"ID: {chunk['id']}")
        print(f"Arabic: {chunk['text_ar'][:300]}")
        print(f"English: {chunk['text_en'][:300]}")


if __name__ == "__main__":
    main()