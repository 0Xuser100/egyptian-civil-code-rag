#!/usr/bin/env python3
"""Extract the bilingual Egyptian Civil Code PDF into article-level JSON and Markdown.

The extractor follows the table-cell workflow in egyptian-civil-code-extraction-report.pdf:
find ruled tables with PyMuPDF, extract each cell by its bounding box, and keep separate
English and Arabic article cursors so a continuation in one column does not shift the other.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import pymupdf

ARABIC_RE = re.compile(r"[\u0600-\u06ff\ufb50-\ufdff\ufe70-\ufeff]")
ARABIC_WORD_RE = re.compile(r"[\u0621-\u064a]+")
ARABIC_ARTICLE_WORD = "\u0645\u0627\u062f\u0629"  # مادة
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
ARABIC_DIGIT_RUN_RE = re.compile(r"[\u0660-\u0669\u06f0-\u06f9]+")
DIACRITICS_RE = re.compile(r"[\u064b-\u0652\u0670]")
TATWEEL = "\u0640"
LAM = "\u0644"
LAM_ALEF_TAILS = "\u0627\u0623\u0625\u0622"  # \u0627 \u0623 \u0625 \u0622

EN_ARTICLE_RE = re.compile(r"^\s*(?:A?rticle|Art\.)\s*(\d{1,4})\b", re.IGNORECASE)
# PDF text extraction splits some Arabic labels with one space inside the word
# (for example, "ما دة" for 439) or inside the number ("٦٠ ١" for 601). Accept
# those splits only when the label word and the 1-4 digit number each fill a line.
AR_SPLIT_ARTICLE_RE = re.compile(
    r"^\s*م[ \t]?ا[ \t]?د[ \t]?ة[ \t]*\n[ \t]*"
    r"([٠-٩۰-۹](?:[ \t]?[٠-٩۰-۹]){0,3})[ \t]*(?:\n|$)"
)
EN_RANGE_RE = re.compile(
    r"\bArticles?\s+(\d{1,4})\s*(?:-|–|—|to)\s*(\d{1,4})"
    r"[\s\S]{0,160}?\brepealed\b",
    re.IGNORECASE,
)
EN_SINGLE_REPEALED_RE = re.compile(
    # Only recognize a repeal statement attached directly to the article label.
    # A loose search catches ordinary provisions such as Article 2, which says
    # that a law may be repealed by a later law.
    r"^\s*Article\s+(\d{1,4})\s+(?:(?:has|is|was)\s+)?repealed\b",
    re.IGNORECASE | re.MULTILINE,
)
EN_HEADING_PATTERNS = (
    (
        "part",
        re.compile(r"^(?:PRELIMINARY|FIRST|SECOND|THIRD|FOURTH|FIFTH)\s+PART\b", re.IGNORECASE),
    ),
    ("book", re.compile(r"^BOOK\s+[IVXLCDM0-9]+\b", re.IGNORECASE)),
    ("chapter", re.compile(r"^CHAPTER\s+[IVXLCDM0-9]+\b", re.IGNORECASE)),
    ("section", re.compile(r"^SECTION\s+[IVXLCDM0-9]+\b", re.IGNORECASE)),
    ("part", re.compile(r"^PRELIMINARY\s+(?:SECTION|TITLE|CHAPTER)\b", re.IGNORECASE)),
    ("topic", re.compile(r"^\s*\d{1,2}[.)-]\s+[A-Z][^.!?]{2,110}:?$")),
)
AR_HEADING_PATTERNS = (
    ("part", re.compile(r"^\s*(?:\u0627\u0644)?\u0642\u0633\u0645\b")),  # section/part
    ("book", re.compile(r"^\s*(?:\u0627\u0644)?\u0643\u062a\u0627\u0628\b")),
    ("chapter", re.compile(r"^\s*(?:\u0627\u0644)?\u0628\u0627\u0628\b")),
    ("section", re.compile(r"^\s*(?:\u0627\u0644)?\u0641\u0635\u0644\b")),
)
LEVELS = ("part", "book", "chapter", "section", "topic")
OUTPUT_FIELDS = (
    "id",
    "scope",
    "article_number",
    "book",
    "chapter",
    "section",
    "topic",
    "text_ar",
    "text_en",
    "arabic_norm",
    "is_repealed",
    "repealed_range",
    "repeal_note",
    "source_page",
    "source_pages",
    "citation",
    "hierarchy_en",
    "hierarchy_ar",
    "flags",
)


def normalize_digits(text: str) -> str:
    return text.translate(ARABIC_DIGITS)


def restore_arabic_digit_order(text: str) -> tuple[str, bool]:
    """Repair Arabic-Indic digit runs returned in visual rather than logical order."""
    restored = ARABIC_DIGIT_RUN_RE.sub(lambda match: match.group(0)[::-1], text)
    return restored, restored != text


def clean_source_text(text: str) -> str:
    """Normalize spacing while preserving the source's Arabic wording and glyph order."""
    text = unicodedata.normalize("NFKC", text).replace(TATWEEL, "")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def arabic_search_text(text: str) -> str:
    text = DIACRITICS_RE.sub("", unicodedata.normalize("NFKC", text))
    text = text.replace(TATWEEL, "")
    return text.translate(
        str.maketrans(
            {"\u0622": "\u0627", "\u0623": "\u0627", "\u0625": "\u0627", "\u0649": "\u064a"}
        )
    ).translate(ARABIC_DIGITS)


def classify_cell(text: str) -> str | None:
    if not text.strip():
        return None
    arabic_count = len(ARABIC_RE.findall(text))
    if arabic_count / max(len(text), 1) >= 0.18:
        return "ar"
    if re.search(r"[A-Za-z]", text):
        return "en"
    return None


def line_text(chars: list[dict[str, Any]]) -> str:
    """Join a text line's characters, restoring the logical order of lam-alef ligatures.

    The source font maps each lam-alef ligature glyph to lam plus a zero-width alef
    placed at lam's right edge, and PyMuPDF emits that alef first, so "لا" reads as
    "ال". The zero width and shared edge separate a ligature from a real "ال".
    """
    text: list[str] = []
    index = 0
    while index < len(chars):
        char = chars[index]
        following = chars[index + 1] if index + 1 < len(chars) else None
        if (
            following is not None
            and char["c"] in LAM_ALEF_TAILS
            and following["c"] == LAM
            and char["bbox"][0] == char["bbox"][2]
            and abs(following["bbox"][2] - char["bbox"][0]) < 0.01
        ):
            text += [LAM, char["c"]]
            index += 2
        else:
            text.append(char["c"])
            index += 1
    return "".join(text)


def cell_text(page: pymupdf.Page, cell: tuple[float, float, float, float] | None) -> str:
    if not cell:
        return ""
    blocks = page.get_text("rawdict", clip=pymupdf.Rect(cell))["blocks"]
    lines = (
        line_text([char for span in line["spans"] for char in span["chars"]])
        for block in blocks
        for line in block.get("lines", [])
    )
    return clean_source_text("\n".join(lines))


def extract_row_texts(page: pymupdf.Page, cells: list[Any]) -> dict[str, str]:
    chunks: dict[str, list[str]] = {"en": [], "ar": []}
    arabic_digits_reversed = False
    for cell in cells:
        text = cell_text(page, cell)
        language = classify_cell(text)
        if language == "ar":
            text, corrected = restore_arabic_digit_order(text)
            arabic_digits_reversed = arabic_digits_reversed or corrected
        if language and text not in chunks[language]:
            chunks[language].append(text)
    return {
        **{language: "\n".join(values).strip() for language, values in chunks.items()},
        "_ar_digits_reversed": arabic_digits_reversed,
    }


def detect_article(text: str, language: str) -> int | None:
    if language == "en":
        match = EN_ARTICLE_RE.match(text)
        return int(match.group(1)) if match else None

    split_match = AR_SPLIT_ARTICLE_RE.match(text)
    if split_match:
        return int(normalize_digits(re.sub(r"[ \t]", "", split_match.group(1))))
    normalized = normalize_digits(text)
    prefix = re.sub(r"^[\s(\[{]+", "", normalized[:100])
    # The source labels Arabic provisions with the article word; accepting either
    # word-first or parenthesized-number-first covers the known layout variants.
    word_match = re.match(
        rf"(?:\u0627\u0644)?{ARABIC_ARTICLE_WORD}\s*[([{{]?\s*(\d{{1,4}})", prefix
    )
    if word_match:
        return int(word_match.group(1))
    number_first = re.match(
        rf"[([{{]\s*(\d{{1,4}})\s*[)\]}}]\s*(?:\u0627\u0644)?{ARABIC_ARTICLE_WORD}",
        prefix,
    )
    if number_first:
        return int(number_first.group(1))
    return None


def detect_heading(text: str, language: str) -> tuple[str, str] | None:
    first_line = text.splitlines()[0].strip() if text.strip() else ""
    if language == "en":
        for level, pattern in EN_HEADING_PATTERNS:
            if pattern.match(first_line):
                return level, first_line
        return None
    for level, pattern in AR_HEADING_PATTERNS:
        if pattern.match(first_line):
            return level, first_line
    # Capture lower-level Arabic topic headings (for example, numbered subtopics).
    if re.match(
        r"^\s*(?:\u0623\u0648\u0644\u0627|\u062b\u0627\u0646\u064a\u0627|\u062b\u0627\u0644\u062b\u0627|\u0631\u0627\u0628\u0639\u0627)\s*[:：-]",
        first_line,
    ):
        return "topic", first_line
    return None


def empty_record(scope: str, number: int) -> dict[str, Any]:
    return {
        "id": f"{scope}-{number:04d}",
        "scope": scope,
        "article_number": number,
        "book": None,
        "chapter": None,
        "section": None,
        "topic": None,
        "text_ar": "",
        "text_en": "",
        "arabic_norm": "",
        "is_repealed": False,
        "repealed_range": None,
        "repeal_note": None,
        "source_page": None,
        "source_pages": [],
        "citation": f"Egyptian Civil Code, Article {number}",
        "hierarchy_en": {},
        "hierarchy_ar": {},
        "flags": [],
    }


def append_text(record: dict[str, Any], language: str, text: str, page_number: int) -> None:
    if language == "en":
        # The source PDF clips the leading "A" from the English label for 452.
        text = re.sub(r"(?im)^rticle(?=\s+\d{1,4}\b)", "Article", text, count=1)
    key = "text_en" if language == "en" else "text_ar"
    if text:
        if record[key] and not record[key].endswith(text):
            record[key] += "\n" + text
        elif not record[key]:
            record[key] = text
    if page_number not in record["source_pages"]:
        record["source_pages"].append(page_number)
    if record["source_page"] is None:
        record["source_page"] = page_number


def set_hierarchy(record: dict[str, Any], language: str, hierarchy: dict[str, str]) -> None:
    record[f"hierarchy_{language}"] = dict(hierarchy)
    for level in LEVELS:
        record[level] = record["hierarchy_en"].get(level) or record["hierarchy_ar"].get(level)


def add_repealed_records(
    records: dict[tuple[str, int], dict[str, Any]],
    scope: str,
    start: int,
    end: int,
    note: str,
    page_number: int,
) -> None:
    lo, hi = sorted((start, end))
    for number in range(lo, hi + 1):
        key = (scope, number)
        record = records.setdefault(key, empty_record(scope, number))
        record["is_repealed"] = True
        record["repealed_range"] = [lo, hi]
        record["repeal_note"] = note
        if page_number not in record["source_pages"]:
            record["source_pages"].append(page_number)
        if record["source_page"] is None:
            record["source_page"] = page_number


def parse_document(input_pdf: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    document = pymupdf.open(input_pdf)
    records: dict[tuple[str, int], dict[str, Any]] = {}
    # The supplied PDF has two Arabic-only issuing-law provisions in a separate
    # full-width box above the Code table on page 1. This Project 2 corpus is
    # intentionally scoped to the Civil Code table; those provisions must be
    # emitted under a separate scope if the corpus expands to the issuing law.
    scope = "code"
    current: dict[str, tuple[str, int] | None] = {"en": None, "ar": None}
    hierarchy: dict[str, dict[str, str]] = {"en": {}, "ar": {}}
    orphan_rows: list[dict[str, Any]] = []
    pages_with_tables = 0
    table_rows = 0
    empty_cells = 0
    repealed_mentions = 0
    rows_with_reversed_arabic_digit_order = 0

    for page_index, page in enumerate(document):
        page_number = page_index + 1
        finder = page.find_tables(strategy="lines")
        if finder.tables:
            pages_with_tables += 1

        for table in finder.tables:
            for row in table.rows:
                table_rows += 1
                empty_cells += sum(cell is None for cell in row.cells)
                row_text = extract_row_texts(page, row.cells)
                if row_text["_ar_digits_reversed"]:
                    rows_with_reversed_arabic_digit_order += 1
                if not row_text["en"] and not row_text["ar"]:
                    continue

                # Switch to the Civil Code at its preliminary heading. If table
                # headings are missing, a repeated Article 1 marks the new scope.
                if re.search(
                    r"\bPRELIMINARY\s+(?:SECTION|TITLE|CHAPTER)\b|\bCIVIL\s+CODE\b",
                    row_text["en"],
                    re.IGNORECASE,
                ):
                    scope = "code"
                    current = {"en": None, "ar": None}
                if "\u0627\u0644\u062a\u0645\u0647\u064a\u062f\u064a" in row_text["ar"]:
                    scope = "code"
                    current = {"en": None, "ar": None}

                row_article: dict[str, int | None] = {}
                row_heading: dict[str, tuple[str, str] | None] = {}
                for language in ("en", "ar"):
                    text = row_text[language]
                    row_heading[language] = detect_heading(text, language)
                    if row_heading[language]:
                        level, title = row_heading[language]
                        hierarchy[language][level] = title
                        for deeper in LEVELS[LEVELS.index(level) + 1 :]:
                            hierarchy[language].pop(deeper, None)
                        if language == "en" and level == "part" and "PRELIMINARY" in title.upper():
                            scope = "code"
                        if (
                            language == "ar"
                            and "\u0627\u0644\u062a\u0645\u0647\u064a\u062f\u064a" in title
                        ):
                            scope = "code"
                    row_article[language] = detect_article(text, language)

                english = row_text["en"]
                range_match = EN_RANGE_RE.search(english)
                single_match = EN_SINGLE_REPEALED_RE.search(english)
                if range_match:
                    start, end = map(int, range_match.groups())
                    add_repealed_records(records, scope, start, end, english, page_number)
                    repealed_mentions += 1
                elif single_match:
                    number = int(single_match.group(1))
                    add_repealed_records(records, scope, number, number, english, page_number)
                    repealed_mentions += 1

                for language in ("en", "ar"):
                    text = row_text[language]
                    if not text or row_heading[language]:
                        continue
                    number = row_article[language]
                    if number is not None:
                        key = (scope, number)
                        record = records.setdefault(key, empty_record(scope, number))
                        if record[f"text_{language}"] and current[language] != key:
                            record["flags"].append(f"duplicate_{language}_article_label")
                        set_hierarchy(record, language, hierarchy[language])
                        current[language] = key
                    key = current[language]
                    if key is None:
                        orphan_rows.append({"page": page_number, "language": language})
                        continue
                    record = records.setdefault(key, empty_record(*key))
                    set_hierarchy(record, language, hierarchy[language])
                    append_text(record, language, text, page_number)

    code_numbers = {number for record_scope, number in records if record_scope == "code"}
    missing_article_numbers = sorted(set(range(1, 1150)) - code_numbers)
    for number in missing_article_numbers:
        gap = records.setdefault(("code", number), empty_record("code", number))
        gap["flags"].append("number_gap_in_source")

    articles = sorted(
        records.values(),
        key=lambda item: (item["scope"] != "issuing_law", item["article_number"]),
    )
    for record in articles:
        record["arabic_norm"] = arabic_search_text(record["text_ar"])
        record["source_pages"].sort()
        if not record["text_en"] and not record["is_repealed"]:
            record["flags"].append("missing_en")
        if not record["text_ar"] and not record["is_repealed"]:
            record["flags"].append("missing_ar")
        record["flags"] = sorted(set(record["flags"]))

    stats = {
        "source_pdf": input_pdf.name,
        "source_sha256": hashlib.sha256(input_pdf.read_bytes()).hexdigest(),
        "page_count": len(document),
        "pages_with_tables": pages_with_tables,
        "table_rows": table_rows,
        "empty_table_cells": empty_cells,
        "rows_with_reversed_arabic_digit_order": rows_with_reversed_arabic_digit_order,
        "article_records": len(articles),
        "issuing_law_records": sum(a["scope"] == "issuing_law" for a in articles),
        "civil_code_records": sum(a["scope"] == "code" for a in articles),
        "repealed_records": sum(a["is_repealed"] for a in articles),
        "repealed_mentions": repealed_mentions,
        "orphan_row_count": len(orphan_rows),
        "records_missing_english": sum("missing_en" in a["flags"] for a in articles),
        "records_missing_arabic": sum("missing_ar" in a["flags"] for a in articles),
        "records_with_flags": sum(bool(a["flags"]) for a in articles),
        "missing_code_article_numbers": missing_article_numbers,
        "records_missing_english_ids": [a["id"] for a in articles if "missing_en" in a["flags"]],
        "records_missing_arabic_ids": [a["id"] for a in articles if "missing_ar" in a["flags"]],
    }
    stats["orphan_pages"] = sorted({row["page"] for row in orphan_rows})
    return articles, stats


def write_json(articles: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [{key: article[key] for key in OUTPUT_FIELDS} for article in articles]
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


def markdown_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\r", "")


def write_markdown(
    articles: list[dict[str, Any]], stats: dict[str, Any], output_path: Path
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Egyptian Civil Code Extraction",
        "",
        f"Source: `{stats['source_pdf']}`  ",
        f"SHA-256: `{stats['source_sha256']}`  ",
        "Method: PyMuPDF table detection with `strategy=lines`; text extracted from each cell bounding box.",
        "",
        "## Extraction Summary",
        "",
        "| Measure | Result |",
        "|---|---:|",
    ]
    labels = {
        "page_count": "PDF pages",
        "pages_with_tables": "Pages with detected tables",
        "table_rows": "Table rows inspected",
        "rows_with_reversed_arabic_digit_order": "Rows where Arabic digit order was restored",
        "article_records": "Article records exported",
        "issuing_law_records": "Issuing-law records",
        "civil_code_records": "Civil Code records",
        "repealed_records": "Records marked repealed",
        "missing_code_article_numbers": "Missing Civil Code article numbers (1–1149)",
        "orphan_row_count": "Rows without an article context",
        "records_missing_english": "Records missing English text",
        "records_missing_arabic": "Records missing Arabic text",
        "records_with_flags": "Records with validation flags",
    }
    for key, label in labels.items():
        lines.append(f"| {label} | {stats[key]} |")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- One JSON record is emitted per article number and scope.",
            "- `source_page` is the first page where the record was seen; `source_pages` includes continuation pages.",
            "- Arabic spelling is preserved in `text_ar`; Arabic-Indic digit runs are restored to logical order. `arabic_norm` is a separate search form.",
            "- `scope` distinguishes articles in the issuing law from articles in the Civil Code.",
            "- Rows without an article context are counted here and are not silently attached to an unrelated article.",
            "",
            "## Review Flags",
            "",
            f"- Source article numbers absent from the PDF: {', '.join(map(str, stats['missing_code_article_numbers'])) or 'none'}.",
            f"- Records with no extracted Arabic text: {', '.join(map(str, stats['records_missing_arabic_ids'])) or 'none'}.",
            f"- Records with no extracted English text: {', '.join(map(str, stats['records_missing_english_ids'])) or 'none'}.",
            f"- Unattached table rows occur on pages: {', '.join(map(str, stats['orphan_pages'])) or 'none'}.",
            "",
            "## Articles",
            "",
        ]
    )
    for article in articles:
        lines.append(f"### {markdown_escape(article['citation'])}")
        lines.append("")
        lines.append(f"- Scope: `{article['scope']}`")
        lines.append(
            f"- Source page: {article['source_page'] if article['source_page'] is not None else 'not found'}"
        )
        if article["source_pages"]:
            lines.append(f"- Source pages: {', '.join(map(str, article['source_pages']))}")
        lines.append(f"- Repealed: {'yes' if article['is_repealed'] else 'no'}")
        if article["repealed_range"]:
            lines.append(
                f"- Repealed range: {article['repealed_range'][0]}–{article['repealed_range'][1]}"
            )
        if article["repeal_note"]:
            lines.append(f"- Repeal note: {markdown_escape(article['repeal_note'])}")
        if article["flags"]:
            lines.append(f"- Flags: {', '.join(f'`{flag}`' for flag in article['flags'])}")
        for language, heading in (("en", "English text"), ("ar", "Arabic text")):
            lines.extend(["", f"#### {heading}", ""])
            value = article["text_en" if language == "en" else "text_ar"]
            lines.append(value if value else "_No text extracted._")
        lines.append("")
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input_pdf", nargs="?", type=Path, default=Path("data/raw/egyption-low.pdf")
    )
    parser.add_argument(
        "--json",
        dest="json_path",
        type=Path,
        default=Path("data/processed/egyptian_civil_code.json"),
    )
    parser.add_argument(
        "--markdown",
        dest="markdown_path",
        type=Path,
        default=Path("data/processed/egyptian_civil_code.md"),
    )
    args = parser.parse_args()
    if not args.input_pdf.is_file():
        parser.error(f"Input PDF not found: {args.input_pdf}")

    articles, stats = parse_document(args.input_pdf)
    write_json(articles, args.json_path)
    write_markdown(articles, stats, args.markdown_path)
    print(
        json.dumps(
            {
                **stats,
                "json_output": str(args.json_path),
                "markdown_output": str(args.markdown_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
