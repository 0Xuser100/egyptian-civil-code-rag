from pathlib import Path

EMBEDDING_MODEL = "BAAI/bge-m3"
LLM_MODEL = "qwen2.5:3b"

INDEX_PATH = Path("data/processed/civil_code.faiss")
CHUNKS_PATH = Path("data/processed/rag_chunks.json")

TOP_K = 5
EMBEDDING_DIMENSION = 1024

MLFLOW_EXPERIMENT = "egyptian-civil-code-rag"
