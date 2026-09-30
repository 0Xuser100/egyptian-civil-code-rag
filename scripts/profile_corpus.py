import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS_PATH = ROOT / "data" / "processed" / "egyptian_civil_code.json"


def main():
    with CORPUS_PATH.open("r", encoding="utf-8") as file:
        records = json.load(file)

    # Check empty language fields by repeal status
    for language, field in [("Arabic", "text_ar"), ("English", "text_en")]:
        empty_records = [
            record
            for record in records
            if not (record.get(field) or "").strip()
        ]

        repealed_empty = [
            record
            for record in empty_records
            if record.get("is_repealed") is True
        ]

        active_empty = [
            record
            for record in empty_records
            if record.get("is_repealed") is not True
        ]

        print(f"\n{language} empty records:")
        print(f"  Total: {len(empty_records)}")
        print(f"  Repealed: {len(repealed_empty)}")
        print(f"  Not marked repealed: {len(active_empty)}")
        print(
            "  Not-repealed IDs:",
            [record.get("id") for record in active_empty],
        )

    print(f"\nTotal records: {len(records)}")

    # Check duplicate identifiers and article numbers
    duplicate_ids = [
        value
        for value, count in Counter(
            record.get("id") for record in records
        ).items()
        if count > 1
    ]

    duplicate_articles = [
        value
        for value, count in Counter(
            record.get("article_number") for record in records
        ).items()
        if count > 1
    ]

    print(f"Duplicate IDs: {duplicate_ids}")
    print(f"Duplicate article numbers: {duplicate_articles}")

    # Check required fields
    required_fields = [
        "id",
        "article_number",
        "text_ar",
        "text_en",
        "source_page",
        "citation",
    ]

    missing_fields = {
        field: sum(
            record.get(field) is None or record.get(field) == ""
            for record in records
        )
        for field in required_fields
    }

    print(f"Missing required fields: {missing_fields}")

    # Check language coverage
    empty_arabic = [
        record.get("id")
        for record in records
        if not (record.get("text_ar") or "").strip()
    ]

    empty_english = [
        record.get("id")
        for record in records
        if not (record.get("text_en") or "").strip()
    ]

    print(f"Empty Arabic count: {len(empty_arabic)}")
    print(f"Empty English count: {len(empty_english)}")

    # Check records requiring review
    flagged_records = [
        record
        for record in records
        if record.get("flags")
    ]

    print(f"Flagged records: {len(flagged_records)}")

    # Detailed review of non-repealed records with missing Arabic
    print("\nRecords requiring Arabic review:")

    review_records = [
        record
        for record in records
        if not (record.get("text_ar") or "").strip()
        and record.get("is_repealed") is not True
    ]

    for record in review_records:
        print("-" * 60)
        print(f"ID: {record.get('id')}")
        print(f"Article: {record.get('article_number')}")
        print(f"Source page: {record.get('source_page')}")
        print(f"English text:\n{record.get('text_en')}")
        print(f"Flags: {record.get('flags')}")

    # List all flagged record IDs
    print("\nFlagged record IDs:")
    for record in flagged_records:
        print(f"- {record.get('id')}: {record.get('flags')}")


if __name__ == "__main__":
    main()