# Extraction Review

## Source and method

The supplied `egyption-low.pdf` is a 170-page, bilingual Arabic/English Civil Code PDF with a native text layer and ruled two-column tables. The extraction report recommends PyMuPDF 1.24 or newer, `page.find_tables(strategy="lines")`, and per-cell text extraction using the cell bounding box. It warns that whole-page extraction can interleave columns and that Arabic-Indic digit runs can be returned in visual order. The current extractor uses this table-cell method, maintains independent language cursors, normalizes Unicode, restores reversed digit runs and lam-alef ligature order, records page provenance, and does not use OCR or pdfplumber.

## Current run measurements

Validated environment: Python 3.13.2 and PyMuPDF 1.28.2, resolved through `uv.lock`. Outputs use UTF-8 with LF line endings on every platform so DVC checksums remain stable between Windows and Linux.

The corrected run inspected 170 pages, found tables on all 170 pages, and processed 1,483 table rows. It counted 72 empty cells and restored Arabic digit order on 997 rows. It emitted 1,149 Civil Code records for article numbers 1 through 1,149. These are extraction counts, not an accuracy score.

After correction, explicit repeal ranges cover 56 articles: 54-80 and 389-417. The first run reported article 1022 as absent because its English label is printed as `Article1022` without a space. The parser now accepts that form; Article 1022 is found on source PDF page 147 with English text, but its Arabic cell is empty. There is no unexplained Code article-number gap in the regenerated corpus.

## Defects found and changes in this branch

1. **False repeal on Article 2.** The original loose single-article regex searched forward for the word “repealed” and marked Article 2 as repealed because its body explains when a law may be repealed. The rule now requires an explicit repeal statement directly attached to an article label. The actual repeal ranges continue to be detected from explicit range notes.
2. **Clipped label on Article 452.** The source text layer starts the English label with `rticle 452`. The extractor now restores the missing leading `A` in that label while preserving the provision text.
3. **Topic hierarchy was empty.** The previous parser did not recognize numbered English topic headings, leaving every `topic` value empty. It now recognizes short numbered heading rows; the regenerated corpus contains topic metadata on 812 records, including Article 147, and tests cover this case.
4. **Separate issuing-law provisions on page 1.** The source has two Arabic-only enactment-law provisions in a full-width box above the Civil Code table. This Project 2 export intentionally includes only the Civil Code table (`scope=code`), so they are not merged with Code Articles 1 and 2. If the corpus later includes them, give them a separate `scope=issuing_law` after reviewing the block boundaries.
5. **Arabic article labels split by extraction.** Several Arabic labels contain spaces inside the word or number (for example, `ما دة` and `٦٠ ١`). Article 601's label (`مادة` / `٦٠ ١`) was read as repealed Article 60, and the other 13 split labels were not detected, so their text was appended to the preceding article. The parser now accepts one space inside the label word or number only when the label and its 1-4 digit number each occupy their own line. Tests cover the observed forms, reject labels split across lines, and check that each recovered record's Arabic label matches its article number and that Article 60 has no Arabic text.

## Coverage and limitations

The Code has 1,093 non-repealed article records. The committed extraction has English text for all 1,093 and Arabic text for 1,092 (99.91% coverage). Article 1022 is the remaining Arabic gap. The previous 14 gaps now have extracted text under the corresponding article numbers; this improves coverage but does not establish transcription accuracy. Repealed-range records intentionally contain the repeal note rather than ordinary article text.

The source report's main recommendation conflicts with its own PyMuPDF 1.28 post-test caveat about reversed digits and corrupted Arabic ligatures. The current script repairs digit-run order and restores lam-alef ligature order from glyph geometry, but does not include the report's unprovided `rtl_safe_extract.py`; visual Arabic text checks remain necessary. On source pages 147-148, English Article 1022 has no matching Arabic cell, while highlighted Arabic paragraphs appear under the neighboring Article 1021 row. Do not move that text between articles without legal review.

These are language-text coverage rates, not transcription accuracy, translation accuracy, or RAG quality. A targeted visual check confirmed the boundaries of the 14 recovered articles; see `extraction-accuracy-review.md`. The separate reproducible 20-article sample remains unchecked before corpus approval. Do not silently fill the Article 1022 gap with generated text.

The output is a JSON array. The handbook specifies the per-article fields but does not require JSONL serialization; the extraction report's JSONL example is an alternate storage format. The current array includes every required handbook field plus provenance and validation metadata. `source_page` is the physical page in this exact PDF; Article 147 is on page 16 here even though the handbook example shows page 34. Use article number for citations, not source page.

## Before embedding

- Visually compare at least 20 randomly selected Arabic/English article pairs to the source PDF.
- Review all flagged records, especially the missing Arabic records and the Article 1021/1022 divergence.
- Confirm hierarchy fields (book, chapter, section, topic) against the source headings.
- Freeze the reviewed JSON and source checksum as a corpus version.
- Only then build language-specific article chunks and evaluate retrieval in both languages.
