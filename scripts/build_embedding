
import json
import time
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-m3"
CHUNKS_PATH = Path("data/processed/rag_chunks.json")
OUTPUT_PATH = Path("data/processed/embeddings.npy")


def main() -> None:
    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME, device="cpu")

    with CHUNKS_PATH.open("r", encoding="utf-8") as file:
        chunks = json.load(file)

    texts = [chunk["embedding_text"] for chunk in chunks]

    print(f"Embedding {len(texts)} chunks...")

    start = time.perf_counter()

    embeddings = model.encode(
        texts,
        batch_size=2,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    elapsed = time.perf_counter() - start

    embeddings = np.asarray(embeddings, dtype=np.float32)

    np.save(OUTPUT_PATH, embeddings)

    print("\n===== EMBEDDING SUMMARY =====")
    print(f"Chunks: {len(chunks)}")
    print(f"Embedding shape: {embeddings.shape}")
    print(f"Embedding dimension: {embeddings.shape[1]}")
    print(f"Time: {elapsed:.2f} seconds")
    print(f"Average per chunk: {elapsed / len(chunks):.2f} seconds")
    print(f"Saved to: {OUTPUT_PATH}")
    print("============================")


if __name__ == "__main__":
    main()