# Extraction Accuracy Review

## Scope

This is an initial manual review of the 14 Arabic article records recovered by the `di-data` parser change. The sample targets the prior article-boundary failures; it is not a random or representative sample of the full corpus. Source pages were rendered and checked against the article labels and table rows.

## Article-boundary check

| Article | Source PDF page(s) | Label appears in the matching Arabic row | Result |
|---:|---:|---|---|
| 439 | 56 | Yes | Pass |
| 543 | 72 | Yes | Pass |
| 601 | 81 | Yes | Pass; Article 60 no longer contains this text |
| 615 | 83-84 | Yes | Pass |
| 627 | 85 | Yes | Pass |
| 652 | 89 | Yes | Pass |
| 660 | 90 | Yes | Pass |
| 703 | 99 | Yes | Pass |
| 855 | 122 | Yes | Pass |
| 966 | 139 | Yes | Pass |
| 1005 | 145 | Yes | Pass |
| 1088 | 159 | Yes | Pass |
| 1092 | 160 | Yes | Pass |
| 1118 | 164 | Yes | Pass |

Observed targeted article-boundary accuracy: **14/14 (100%)**. This measures only whether these recovered passages were assigned to the correct article rows; it does not measure whole-corpus boundary accuracy.

The handbook's fixed 20-article sample (seed `20260928`) was also rendered and checked for article-label placement and Arabic/English row pairing. All **20/20 (100%)** sampled labels appeared in the expected table rows. This was a boundary/pairing check; the complete article text, hierarchy, and citation were not transcribed or verified line by line, so the checklist's full-text review remains pending.

## Character-level transcription check

Article 543 on source PDF page 72 was manually transcribed from the rendered Arabic table cell. The reference body is:

> ينتهي القرض بانتهاء الميعاد المتفق عليه.

The extracted body is:

> ينتهي القرض بإ\nنه\nاء الميعاد المتفق عليه.

Using Levenshtein character distance after removing all whitespace from both strings, the reference has 35 characters and the extraction has **2 character edits**: **CER = 2/35 = 5.71%**. With whitespace collapsed to single spaces instead of removed, the score is **4/40 = 10.00%**, reflecting both character errors and broken word spacing. The extracted phrase also visibly breaks one word across three lines.

This one short passage is a diagnostic example, not a corpus accuracy estimate. A representative transcription-accuracy score requires a larger manually transcribed gold sample. The 20-article sample's line-by-line text, hierarchy, and citation review remains to be completed.

## Remaining review

- Article 1022 remains without extracted Arabic text. Pages 147-148 show highlighted Arabic text adjacent to English Article 1022 under the Article 1021 area; it was not reassigned.
- Article 615 includes a glyph in the extracted text that needs close transcription review.
- The 14 boundary checks do not validate every character of the 3,354 extracted Arabic characters.
- Coverage (1,092/1,093 active records with Arabic text) is not transcription accuracy, translation accuracy, or RAG quality.
