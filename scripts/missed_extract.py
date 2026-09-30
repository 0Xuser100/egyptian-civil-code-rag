from pathlib import Path

import pymupdf

from egyptian_civil_code_rag.extraction import (
    restore_arabic_digit_order,
    detect_article,
)
import inspect
from egyptian_civil_code_rag import extraction


ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = ROOT / "data" / "raw" / "egyption-low.pdf"

SAMPLES = [
    "٤٣٩ ةدام",
    "٥٤٣ ةدام",
    "٦٠١ ةدام",
    "٦١٥ ةدام",
    "٦٢٧ ةدام",
    "٦٥٢ ةدام",
    "٦٦٠ ةدام",
    "٧٠٣ ةدام",
    "٨٥٥ ةدام",
    "٩٦٦ ةدام",
    "١٠٠٥ ةدام",
    "١٠٢٢ ةدام",
    "١٠٨٨ ةدام",
    "١٠٩٢ ةدام",
    "١١١٨ ةدام",
]


def check_article_detection():
    print("=" * 80)
    print("ARTICLE DETECTION CHECK")
    print("=" * 80)

    for text in SAMPLES:
        restored, corrected = restore_arabic_digit_order(text)
        detected = detect_article(restored, "ar")

        print(
            f"{text!r} -> {restored!r} "
            f"| reversed={corrected} "
            f"| detected={detected}"
        )


def inspect_pdf_page():
    page_number = 85

    print("\n" + "=" * 80)
    print(f"PDF TABLE CHECK - PAGE {page_number}")
    print("=" * 80)

    with pymupdf.open(PDF_PATH) as document:
        page = document[page_number - 1]
        tables = page.find_tables()

        print(f"Number of tables: {len(tables.tables)}")

        for table_number, table in enumerate(tables.tables, start=1):
            print(f"\nTABLE {table_number}")
            print("-" * 80)

            for row_number, row in enumerate(table.extract(), start=1):
                for cell_number, cell in enumerate(row, start=1):
                    if cell and "٦٢٧" in cell:
                        print(f"ROW {row_number}, CELL {cell_number}:")
                        print(repr(cell))

def check_restore_function():
    print("\n" + "=" * 80)
    print("RESTORE FUNCTION CHECK")
    print("=" * 80)

    samples = [
        "٦٢٧ ةدام",
        "Article 627",
        "مادة ٦٢٧",
        "النص العربي ١٢٣",
    ]

    for text in samples:
        restored, changed = restore_arabic_digit_order(text)

        print(f"Original : {text!r}")
        print(f"Restored : {restored!r}")
        print(f"Changed  : {changed}")
        print("-" * 80)                        

def show_restore_usage():
    print("\n" + "=" * 80)
    print("RESTORE FUNCTION USAGE")
    print("=" * 80)

    source = inspect.getsource(extraction)

    for line_number, line in enumerate(source.splitlines(), start=1):
        if "restore_arabic_digit_order(" in line:
            print(f"{line_number}: {line.strip()}")

def check_raw_detection():
    print("\n" + "=" * 80)
    print("RAW ARTICLE DETECTION")
    print("=" * 80)

    samples = [
        "٦٢٥ ةدام",
        "٦٢٦ ةدام",
        "٦٢٧ ةدام",
        "٦٢٨ ةدام",
    ]

    for text in samples:
        detected = detect_article(text, "ar")
        print(f"{text!r} -> detected={detected}")


def test_arabic_marker_pattern():
    print("\n" + "=" * 80)
    print("ARABIC MARKER PATTERN")
    print("=" * 80)

    import re

    pattern = re.compile(
        r"^\s*([٠-٩۰-۹]+)\s*ةدام"
    )

    samples = [
        "٦٢٥ ةدام",
        "٦٢٦ ةدام",
        "٦٢٧ ةدام",
        "١٠٢٢ ةدام",
    ]

    for text in samples:
        match = pattern.match(text)

        if match:
            number = match.group(1)
            print(f"{text!r} -> number={number!r}")
        else:
            print(f"{text!r} -> NO MATCH")  


def check_missing_article_shapes():
    import pymupdf
    from egyptian_civil_code_rag.extraction import extract_row_texts

    pages = [56, 72, 81, 83, 85, 89, 90, 99, 122, 139, 145, 147, 159, 160, 164]

    with pymupdf.open(PDF_PATH) as document:
        print("\n" + "=" * 80)
        print("MISSING ARTICLE SHAPES")
        print("=" * 80)

        for page_number in pages:
            page = document[page_number - 1]
            tables = page.find_tables(strategy="lines").tables

            for table in tables:
                for row in table.rows:
                    row_text = extract_row_texts(page, row.cells)
                    ar = row_text["ar"]

                    if ar:
                        print(f"Page {page_number}: {repr(ar[:80])}")


def test_split_arabic_article_marker():
    import re

    samples = [
        "ما دة\n٤٣٩",
        "ما دة\n٥٤٣",
        "ماد ة\n٦٢٧",
        "م ادة\n١٠٢٢",
        "مادة\n٦٢٨",
    ]

    pattern = re.compile(
        r"^\s*م\s*ا\s*د\s*ة\s*[\r\n\s]*([٠-٩۰-۹]+)"
    )

    print("\n" + "=" * 80)
    print("SPLIT ARABIC ARTICLE MARKER CHECK")
    print("=" * 80)

    for sample in samples:
        match = pattern.match(sample)
        print(repr(sample), "->", match.group(1) if match else None)


def check_missing_article_detection():
    import pymupdf
    from egyptian_civil_code_rag.extraction import extract_row_texts, detect_article

    pages = [56, 72, 81, 83, 85, 89, 90, 99, 122, 139, 145, 147, 159, 160, 164]

    print("\n" + "=" * 80)
    print("MISSING ARTICLES DETECTION CHECK")
    print("=" * 80)

    with pymupdf.open(PDF_PATH) as document:
        for page_number in pages:
            page = document[page_number - 1]

            for table in page.find_tables(strategy="lines").tables:
                for row in table.rows:
                    row_text = extract_row_texts(page, row.cells)
                    ar = row_text["ar"]

                    if not ar:
                        continue

                    number = detect_article(ar, "ar")

                    if number in [439, 543, 601, 615, 627, 652, 660, 703,
                                  855, 966, 1005, 1022, 1088, 1092, 1118]:
                        print(f"Page {page_number}: detected={number}")

def test_article_627_pipeline():
    import pymupdf
    from egyptian_civil_code_rag.extraction import extract_row_texts, detect_article

    with pymupdf.open(PDF_PATH) as document:
        page = document[84]  # PDF page 85
        table = page.find_tables(strategy="lines").tables[0]

        for row_number, row in enumerate(table.rows):
            row_text = extract_row_texts(page, row.cells)

            if "٦٢٧" in row_text["ar"] or "٧٢٦" in row_text["ar"]:
                print("\n" + "=" * 80)
                print("ARTICLE 627 PIPELINE CHECK")
                print("=" * 80)
                print("Arabic extracted:")
                print(repr(row_text["ar"]))
                print("Detected article:")
                print(detect_article(row_text["ar"], "ar"))
                break


def test_spaced_arabic_digits():
    import re

    samples = [
        "مادة\n٦٠ ١",
        "مادة\n١٠٢ ٢",
        "مادة\n١١١ ٨",
    ]

    pattern = re.compile(
        r"^\s*م\s*ا\s*د\s*ة\s*[\r\n\s]*([٠-٩۰-۹]+(?:\s+[٠-٩۰-۹]+)*)"
    )

    print("\n" + "=" * 80)
    print("SPACED ARABIC DIGITS CHECK")
    print("=" * 80)

    for sample in samples:
        match = pattern.match(sample)
        if match:
            number = match.group(1).replace(" ", "")
            print(repr(sample), "->", number)
        else:
            print(repr(sample), "-> None")

def test_article_601():
    import re

    sample = "مادة\n٦٠ ١\n(١ .) ال ينتهي الإيجار بموت المؤجر"

    pattern = re.compile(
        r"^\s*م\s*ا\s*د\s*ة\s*[\r\n\s]*([٠-٩۰-۹]+(?:\s+[٠-٩۰-۹]+)*)"
    )

    match = pattern.match(sample)

    if match:
        number = match.group(1).replace(" ", "")
        number = number.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
        print(f"Article detected: {int(number)}")
    else:
        print("Article detected: None")


test_article_601()

#---------------------------

def inspect_article_1022():
    pdf_path = Path("data/raw/egyption-low.pdf")

    with pymupdf.open(pdf_path) as document:
        for page_number in (147, 148):
            page = document[page_number - 1]

            print("\n" + "=" * 80)
            print(f"PAGE {page_number} - ARABIC CELLS")
            print("=" * 80)

            finder = page.find_tables(strategy="lines")

            for table_index, table in enumerate(finder.tables, start=1):
                print(f"\nTABLE {table_index}")

                for row_index, row in enumerate(table.rows, start=1):
                    print(f"\nROW {row_index}:")

                    for cell_index, cell in enumerate(row.cells, start=1):
                        if cell is None:
                            continue

                        text = page.get_text("text", clip=cell)

                        if text.strip():
                            print(f"\nCELL {cell_index}:")
                            print(repr(text[:500]))


inspect_article_1022()



##############
def inspect_1022_raw_layout():
    pdf_path = Path("data/raw/egyption-low.pdf")

    with pymupdf.open(pdf_path) as document:
        page = document[146]  # page 147

        print("\n" + "=" * 80)
        print("PAGE 147 - RAW TEXT AROUND ARTICLE 1022")
        print("=" * 80)

        words = page.get_text("words")

        for word in words:
            x0, y0, x1, y1, text, block_no, line_no, word_no = word

            if 1020 <= y0 <= 1500:
                print(
                    f"y={y0:.1f}-{y1:.1f} | "
                    f"x={x0:.1f}-{x1:.1f} | "
                    f"{text!r}"
                )


inspect_1022_raw_layout()






if __name__ == "__main__":
    check_article_detection()
    check_restore_function()
    inspect_pdf_page()
    show_restore_usage()
    check_raw_detection()
    test_arabic_marker_pattern()
   
    check_missing_article_shapes()
    test_split_arabic_article_marker()
    check_missing_article_detection()
    test_article_627_pipeline()
    test_spaced_arabic_digits()
   
