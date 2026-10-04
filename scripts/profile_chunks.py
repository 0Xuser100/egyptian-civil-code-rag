

"""Profile RAG chunks before embedding and vector indexing."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from statistics import mean, median


ROOT = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    ROOT
    / "data"
    / "processed"
    / "rag_chunks.json"
)


def load_chunks(path: Path) -> list[dict]:
    """Load exported RAG chunks from JSON."""

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def text_length(text: str) -> int:
    """Return character count after trimming whitespace."""

    return len((text or "").strip())


def count_words(text: str) -> int:
    """Return approximate whitespace-separated word count."""

    return len((text or "").split())


def get_language_presence(page_content: str) -> tuple[bool, bool]:
    """Check whether a chunk contains Arabic and English sections."""

    has_arabic = "Arabic Text:" in page_content
    has_english = "English Text:" in page_content

    return has_arabic, has_english


def main() -> None:
    print("=" * 70)
    print("Egyptian Civil Code RAG Chunk Quality Profile")
    print("=" * 70)

    print("\nInput:")
    print(INPUT_PATH)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Chunk file not found: {INPUT_PATH}"
        )

    chunks = load_chunks(INPUT_PATH)

    print(f"\nTotal chunks: {len(chunks)}")

    if not chunks:
        print("No chunks found.")
        return

    # -------------------------------------------------------------
    # Basic statistics
    # -------------------------------------------------------------

    character_lengths: list[int] = []
    word_lengths: list[int] = []

    arabic_count = 0
    english_count = 0
    bilingual_count = 0
    arabic_only_count = 0
    english_only_count = 0

    for chunk in chunks:
        page_content = chunk.get("page_content", "")

        character_lengths.append(
            text_length(page_content)
        )

        word_lengths.append(
            count_words(page_content)
        )

        has_arabic, has_english = get_language_presence(
            page_content
        )

        if has_arabic:
            arabic_count += 1

        if has_english:
            english_count += 1

        if has_arabic and has_english:
            bilingual_count += 1
        elif has_arabic:
            arabic_only_count += 1
        elif has_english:
            english_only_count += 1

    print("\n" + "-" * 70)
    print("Language distribution")
    print("-" * 70)

    print(f"With Arabic:       {arabic_count}")
    print(f"With English:      {english_count}")
    print(f"Bilingual:         {bilingual_count}")
    print(f"Arabic only:       {arabic_only_count}")
    print(f"English only:      {english_only_count}")

    # -------------------------------------------------------------
    # Character statistics
    # -------------------------------------------------------------

    print("\n" + "-" * 70)
    print("Character length statistics")
    print("-" * 70)

    print(f"Minimum:  {min(character_lengths):,}")
    print(f"Maximum:  {max(character_lengths):,}")
    print(f"Mean:     {mean(character_lengths):,.1f}")
    print(f"Median:   {median(character_lengths):,.1f}")

    # -------------------------------------------------------------
    # Word statistics
    # -------------------------------------------------------------

    print("\n" + "-" * 70)
    print("Word count statistics")
    print("-" * 70)

    print(f"Minimum:  {min(word_lengths):,}")
    print(f"Maximum:  {max(word_lengths):,}")
    print(f"Mean:     {mean(word_lengths):,.1f}")
    print(f"Median:   {median(word_lengths):,.1f}")

    # -------------------------------------------------------------
    # Length buckets
    # -------------------------------------------------------------

    buckets = {
        "< 200 chars": 0,
        "200-499 chars": 0,
        "500-999 chars": 0,
        "1,000-1,999 chars": 0,
        "2,000-3,999 chars": 0,
        ">= 4,000 chars": 0,
    }

    for length in character_lengths:
        if length < 200:
            buckets["< 200 chars"] += 1
        elif length < 500:
            buckets["200-499 chars"] += 1
        elif length < 1000:
            buckets["500-999 chars"] += 1
        elif length < 2000:
            buckets["1,000-1,999 chars"] += 1
        elif length < 4000:
            buckets["2,000-3,999 chars"] += 1
        else:
            buckets[">= 4,000 chars"] += 1

    print("\n" + "-" * 70)
    print("Chunk length distribution")
    print("-" * 70)

    for bucket, count in buckets.items():
        print(f"{bucket:<20} {count}")

    # -------------------------------------------------------------
    # Shortest chunks
    # -------------------------------------------------------------

    indexed_chunks = list(enumerate(chunks))

    shortest = sorted(
        indexed_chunks,
        key=lambda item: text_length(
            item[1].get("page_content", "")
        ),
    )[:10]

    print("\n" + "=" * 70)
    print("10 shortest chunks")
    print("=" * 70)

    for index, chunk in shortest:
        metadata = chunk.get("metadata", {})
        page_content = chunk.get("page_content", "")

        print("-" * 70)
        print(f"Rank: {shortest.index((index, chunk)) + 1}")
        print(f"ID: {metadata.get('id')}")
        print(f"Article: {metadata.get('article_number')}")
        print(f"Source page: {metadata.get('source_page')}")
        print(f"Characters: {len(page_content):,}")
        print(f"Words: {count_words(page_content):,}")
        print(page_content[:700])

    # -------------------------------------------------------------
    # Longest chunks
    # -------------------------------------------------------------

    longest = sorted(
        indexed_chunks,
        key=lambda item: text_length(
            item[1].get("page_content", "")
        ),
        reverse=True,
    )[:10]

    print("\n" + "=" * 70)
    print("10 longest chunks")
    print("=" * 70)

    for rank, (index, chunk) in enumerate(longest, start=1):
        metadata = chunk.get("metadata", {})
        page_content = chunk.get("page_content", "")

        print("-" * 70)
        print(f"Rank: {rank}")
        print(f"ID: {metadata.get('id')}")
        print(f"Article: {metadata.get('article_number')}")
        print(f"Source page: {metadata.get('source_page')}")
        print(f"Characters: {len(page_content):,}")
        print(f"Words: {count_words(page_content):,}")

        preview = page_content[:1200]

        if len(page_content) > 1200:
            preview += "\n...[truncated]..."

        print(preview)

    # -------------------------------------------------------------
    # Check very long chunks
    # -------------------------------------------------------------

    long_threshold = 4000

    very_long = [
        chunk
        for chunk in chunks
        if len(chunk.get("page_content", "")) >= long_threshold
    ]

    print("\n" + "=" * 70)
    print(f"Chunks >= {long_threshold:,} characters")
    print("=" * 70)

    print(f"Count: {len(very_long)}")

    for chunk in very_long:
        metadata = chunk.get("metadata", {})
        page_content = chunk.get("page_content", "")

        print(
            f"- {metadata.get('id')} | "
            f"Article {metadata.get('article_number')} | "
            f"{len(page_content):,} chars"
        )

    # -------------------------------------------------------------
    # Article sequence check
    # -------------------------------------------------------------

    article_numbers = [
        chunk.get("metadata", {}).get("article_number")
        for chunk in chunks
    ]

    print("\n" + "=" * 70)
    print("Article sequence check")
    print("=" * 70)

    duplicates = [
        number
        for number, count in Counter(article_numbers).items()
        if count > 1
    ]

    print(f"Duplicate article numbers: {duplicates}")

    if article_numbers:
        expected = list(
            range(
                min(article_numbers),
                max(article_numbers) + 1,
            )
        )

        missing = sorted(
            set(expected) - set(article_numbers)
        )

        print(f"Missing article numbers: {missing}")

    # -------------------------------------------------------------
    # Metadata checks
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print("Metadata checks")
    print("=" * 70)

    required_metadata = [
        "id",
        "scope",
        "article_number",
        "citation",
        "is_repealed",
        "source_page",
        "source_pages",
        "book",
        "chapter",
        "section",
        "topic",
        "hierarchy_en",
        "hierarchy_ar",
        "flags",
    ]

    metadata_problems = []

    for chunk in chunks:
        metadata = chunk.get("metadata", {})

        missing_fields = [
            field
            for field in required_metadata
            if field not in metadata
        ]

        if missing_fields:
            metadata_problems.append(
                {
                    "id": metadata.get("id"),
                    "missing": missing_fields,
                }
            )

    if metadata_problems:
        print("Metadata problems found:")

        for problem in metadata_problems:
            print(
                f"- {problem['id']}: "
                f"missing {problem['missing']}"
            )
    else:
        print("All chunks contain the expected metadata fields.")

    # -------------------------------------------------------------
    # Empty content check
    # -------------------------------------------------------------

    empty_chunks = [
        chunk
        for chunk in chunks
        if not chunk.get("page_content", "").strip()
    ]

    print(f"\nEmpty chunks: {len(empty_chunks)}")

    # -------------------------------------------------------------
    # Specific Article 1022 check
    # -------------------------------------------------------------

    article_1022 = next(
        (
            chunk
            for chunk in chunks
            if chunk.get("metadata", {}).get("article_number") == 1022
        ),
        None,
    )

    print("\n" + "=" * 70)
    print("Article 1022 quality check")
    print("=" * 70)

    if article_1022:
        metadata = article_1022["metadata"]
        page_content = article_1022["page_content"]

        print(f"ID: {metadata.get('id')}")
        print(f"Arabic present: {'Arabic Text:' in page_content}")
        print(f"English present: {'English Text:' in page_content}")
        print(f"Flags: {metadata.get('flags')}")
        print(f"Characters: {len(page_content):,}")

        print("\nText preview:")
        print(page_content[:1500])

    else:
        print("Article 1022 was not found.")

    # -------------------------------------------------------------
    # Possible extraction artifacts
    # -------------------------------------------------------------

    suspicious_patterns = [
        "Article1022",
        "rticle",
        "f an agreement",
        "the cost",
        "he has always",
        "pa r",
        "  ",
    ]

    print("\n" + "=" * 70)
    print("Possible text artifacts")
    print("=" * 70)

    artifact_hits = []

    for chunk in chunks:
        page_content = chunk.get("page_content", "")
        metadata = chunk.get("metadata", {})

        matched_patterns = [
            pattern
            for pattern in suspicious_patterns
            if pattern in page_content
        ]

        if matched_patterns:
            artifact_hits.append(
                (
                    metadata.get("id"),
                    metadata.get("article_number"),
                    matched_patterns,
                )
            )

    print(f"Chunks with possible artifact patterns: {len(artifact_hits)}")

    for article_id, article_number, patterns in artifact_hits[:30]:
        print(
            f"- {article_id} | "
            f"Article {article_number} | "
            f"patterns={patterns}"
        )

    if len(artifact_hits) > 30:
        print(
            f"... and {len(artifact_hits) - 30} more."
        )

    # -------------------------------------------------------------
    # Final assessment
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print("FINAL PROFILE")
    print("=" * 70)

    print(f"Total chunks: {len(chunks):,}")
    print(f"Arabic chunks: {arabic_count:,}")
    print(f"English chunks: {english_count:,}")
    print(f"Bilingual chunks: {bilingual_count:,}")
    print(f"Very long chunks (>= 4,000 chars): {len(very_long):,}")
    print(f"Empty chunks: {len(empty_chunks):,}")
    print(f"Metadata problems: {len(metadata_problems):,}")

    if not empty_chunks and not metadata_problems:
        print("\nBasic chunk integrity: PASS")

    print("\nNo files were modified.")


if __name__ == "__main__":
    main()
