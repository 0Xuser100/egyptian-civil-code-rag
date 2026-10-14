import json
from pathlib import Path

import faiss
import numpy as np

EMBEDDINGS_PATH = Path("data/processed/embeddings.npy")
CHUNKS_PATH = Path("data/processed/rag_chunks.json")
INDEX_PATH = Path("data/processed/civil_code.faiss")
IDS_PATH = Path("data/processed/chunk_ids.json")


def main() -> None:
    # Load embeddings
    embeddings = np.load(EMBEDDINGS_PATH).astype("float32")

    print(f"Loaded embeddings: {embeddings.shape}")

    # Because embeddings were normalized, inner product = cosine similarity
    index = faiss.IndexFlatIP(embeddings.shape[1])

    index.add(embeddings)

    print(f"FAISS index contains: {index.ntotal} vectors")

    # Save FAISS index
    faiss.write_index(index, str(INDEX_PATH))

    # Save the mapping between FAISS positions and article IDs
    with CHUNKS_PATH.open("r", encoding="utf-8") as file:
        chunks = json.load(file)

    chunk_ids = [chunk["id"] for chunk in chunks]

    if len(chunk_ids) != index.ntotal:
        raise ValueError(
            f"Mismatch: {len(chunk_ids)} chunk IDs "
            f"but {index.ntotal} vectors"
        )

    with IDS_PATH.open("w", encoding="utf-8") as file:
        json.dump(chunk_ids, file, ensure_ascii=False, indent=2)

    print("\n===== FAISS SUMMARY =====")
    print(f"Vectors: {index.ntotal}")
    print(f"Dimension: {index.d}")
    print(f"Index: {INDEX_PATH}")
    print(f"IDs: {IDS_PATH}")
    print("=========================")


if __name__ == "__main__":
    main()