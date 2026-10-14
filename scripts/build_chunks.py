import json
from pathlib import Path

SOURCE_PATH = Path("data/processed/egyptian_civil_code.json")
OUTPUT_PATH = Path("data/processed/rag_chunks.json")


def build_embedding_text(text_ar: str, text_en: str) -> str:
    parts = []

    if text_ar.strip():
        parts.append(text_ar.strip())

    if text_en.strip():
        parts.append(text_en.strip())

    return "\n\n".join(parts)


def main() -> None:
    with SOURCE_PATH.open("r", encoding="utf-8") as file:
        records = json.load(file)

    chunks = []

    for record in records:
        # Skip repealed articles
        if record.get("is_repealed", False):
            continue

        text_ar = record.get("text_ar", "").strip()
        text_en = record.get("text_en", "").strip()

        # Skip only if both languages are empty
        if not text_ar and not text_en:
            continue

        embedding_text = build_embedding_text(
            text_ar=text_ar,
            text_en=text_en,
        )

        chunk = {
            "id": record["id"],
            "article_number": record["article_number"],
            "text_ar": text_ar,
            "text_en": text_en,
            "embedding_text": embedding_text,
            "metadata": {
                "scope": record["scope"],
                "citation": record["citation"],
                "is_repealed": record["is_repealed"],
                "repealed_range": record["repealed_range"],
                "repeal_note": record["repeal_note"],
                "source_page": record["source_page"],
                "source_pages": record["source_pages"],
                "book": record["book"],
                "chapter": record["chapter"],
                "section": record["section"],
                "topic": record["topic"],
                "hierarchy_en": record["hierarchy_en"],
                "hierarchy_ar": record["hierarchy_ar"],
                "flags": record["flags"],
            },
        }

        chunks.append(chunk)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            chunks,
            file,
            ensure_ascii=False,
            indent=2,
        )

    # Basic validation
    bilingual = sum(
        bool(chunk["text_ar"]) and bool(chunk["text_en"])
        for chunk in chunks
    )

    arabic_only = sum(
        bool(chunk["text_ar"]) and not bool(chunk["text_en"])
        for chunk in chunks
    )

    english_only = sum(
        bool(chunk["text_en"]) and not bool(chunk["text_ar"])
        for chunk in chunks
    )

    print(f"Successfully created {len(chunks)} chunks.")
    print()
    print("Chunking summary:")
    print(f"  Total chunks: {len(chunks)}")
    print(f"  Bilingual: {bilingual}")
    print(f"  Arabic only: {arabic_only}")
    print(f"  English only: {english_only}")

    # Check Article 1022
    article_1022 = next(
        chunk
        for chunk in chunks
        if chunk["article_number"] == 1022
    )

    print()
    print("Article 1022 check:")
    print(f"  Arabic length: {len(article_1022['text_ar'])}")
    print(f"  English length: {len(article_1022['text_en'])}")
    print(f"  Flags: {article_1022['metadata']['flags']}")


if __name__ == "__main__":
    main()