# Review Provenance

On 2026-09-28, a separate Claude Code CLI session using `claude-opus-5-5` with `high` effort completed a read-only review of all three supplied PDFs. Session ID: `4ca755ce-121a-4b37-8f67-0ab66b0cf7c9`. It did not edit the repository. The final effort setting follows the user's change from ultra to max to high.

| Input | Use in this project |
|---|---|
| `egyptian-civil-code-extraction-report.pdf` | Table-cell extraction parameters, Arabic text-layer risks, and source-method comparison |
| `egyption-low.pdf` | 170-page bilingual source, physical page provenance, labels and repeal statements |
| `The-MLOps-Practitioner-Handbook-3-tracks.pdf` | Final Project 2 schema, API, experiment, serving, evaluation, monitoring, safety, and delivery requirements |

The source PDF SHA-256 is `2d6419fb262dab712f7bf5f6e31834bea74fbcf03b78ae081dd35d156915eebf`. These filenames remain unchanged locally; only the law dataset has a DVC pointer. The report and handbook are not redistributed in the repository.

The review led to recognizing the no-space Article 1022 label, documenting the separate page 1 issuing-law scope, separating coverage from transcription accuracy, and completing the course delivery map. The branch also corrects Article 2's false repeal, Article 452's clipped label, and numbered topic headings. The current reviewed decisions are in `extraction-review.md` and the architecture documents; the outstanding human checks are in `corpus-review-checklist.md`.

The designs draw on the local `D:\Hakeem-bk` project's modular monolith, configuration, service/repository boundaries, README, and deployment documentation, and on `D:\OrionIntel`'s explicit runtime documentation and vector-store architecture. This small corpus uses one PostgreSQL/pgvector store and offline ingestion; it does not need a worker queue to establish the baseline. No credentials or configuration secrets were copied from either project.

The handbook's inserted pages can make its printed numbering differ from physical PDF page numbering. Corpus `source_page` values always identify the physical page of the supplied law PDF. The stable user citation is the legal article number.
