import json
from pathlib import Path

from egyptian_civil_code_rag.extraction import (
    EN_RANGE_RE,
    EN_SINGLE_REPEALED_RE,
    detect_article,
)

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "data" / "processed" / "egyptian_civil_code.json"


def load_corpus() -> list[dict[str, object]]:
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


def test_article_numbers_and_handbook_fields_are_present() -> None:
    records = load_corpus()
    numbers = [record["article_number"] for record in records]
    assert numbers == list(range(1, 1150))

    required = {
        "article_number",
        "book",
        "chapter",
        "section",
        "topic",
        "text_ar",
        "text_en",
        "is_repealed",
        "source_page",
        "citation",
    }
    assert all(required <= record.keys() for record in records)
    assert all(record["scope"] == "code" for record in records)
    assert all(type(record["article_number"]) is int for record in records)
    assert all(type(record["is_repealed"]) is bool for record in records)
    assert all(type(record["source_page"]) is int for record in records)
    assert all(isinstance(record["text_ar"], str) for record in records)
    assert all(isinstance(record["text_en"], str) for record in records)
    assert all(record["citation"] for record in records)


def test_repeal_detection_requires_an_explicit_statement() -> None:
    article_two = "Article 2\nA provision of a law can only be repealed by a later law."
    assert EN_SINGLE_REPEALED_RE.search(article_two) is None

    explicit = "Article 123 is repealed by Decree No. 1."
    assert EN_SINGLE_REPEALED_RE.search(explicit)

    range_note = "Articles 54-80 have been repealed by Presidential Decree."
    assert EN_RANGE_RE.search(range_note)


def test_english_article_label_without_space_is_detected() -> None:
    assert detect_article("Article1022\nArticle body", "en") == 1022


RECOVERED_ARABIC_ARTICLES = (
    439, 543, 601, 615, 627, 652, 660, 703, 855, 966, 1005, 1088, 1092, 1118
)


def test_split_and_spaced_arabic_article_labels_are_detected() -> None:
    # Label forms observed in the source text layer for the recovered articles.
    cases = {
        "ما دة\n٤٣٩\nنص المادة": 439,
        "ماد ة\n٦٢٧\nنص المادة": 627,
        "م ادة\n١٠٠٥\nنص المادة": 1005,
        "مادة\n٦٠ ١\n(١) نص المادة": 601,
    }
    for text, expected in cases.items():
        assert detect_article(text, "ar") == expected


def test_split_arabic_label_parsing_stays_line_bound() -> None:
    assert detect_article("ما\nدة\n٤٣٩\nنص المادة", "ar") is None
    assert detect_article("مادة\n٦٠\n١ نص المادة", "ar") == 60
    assert detect_article("مادة\n٦٠ ١ نص المادة", "ar") == 60


def test_known_language_gap_and_repeal_ranges_are_visible() -> None:
    records = {record["article_number"]: record for record in load_corpus()}

    assert records[2]["is_repealed"] is False
    assert all(records[number]["is_repealed"] for number in range(54, 81))
    assert all(records[number]["is_repealed"] for number in range(389, 418))
    assert {number for number, record in records.items() if record["is_repealed"]} == (
        set(range(54, 81)) | set(range(389, 418))
    )
    assert all(record["text_en"] for record in records.values() if not record["is_repealed"])
    assert {
        number for number, record in records.items() if "missing_ar" in record["flags"]
    } == {1022}
    # Article 601's spaced label was previously read as repealed Article 60.
    assert not records[60]["text_ar"]
    for number in RECOVERED_ARABIC_ARTICLES:
        assert detect_article(records[number]["text_ar"], "ar") == number
        assert "missing_ar" not in records[number]["flags"]

    article_1022 = records[1022]
    assert article_1022["source_page"] == 147
    assert "missing_ar" in article_1022["flags"]
    assert "missing_en" not in article_1022["flags"]
    assert "number_gap_in_source" not in article_1022["flags"]


def test_clipped_english_article_label_is_normalized() -> None:
    records = {record["article_number"]: record for record in load_corpus()}
    assert records[452]["text_en"].startswith("Article 452")


def test_numbered_topic_heading_is_captured() -> None:
    records = {record["article_number"]: record for record in load_corpus()}
    assert records[147]["topic"] == "2. The Effects of a Contract"
