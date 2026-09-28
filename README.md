# Egyptian Civil Code RAG

An MLOps Project 2 workspace for building a bilingual Arabic and English legal question answering system over article-level Egyptian Civil Code data.

**Current state:** the extraction experiment, corpus review, and end-to-end designs are in place. The `/ask` API, embeddings, vector index, and generation service are the next implementation milestone; this repository does not claim to serve RAG questions yet.

## Project name and structure

Repository name: `egyptian-civil-code-rag`.

```text
.
|-- data/
|   |-- raw/                 # Local source PDF; excluded from Git
|   `-- processed/           # Article JSON and readable Markdown review
|-- docs/
|   |-- architecture/
|   |   |-- high-level-design.md
|   |   `-- low-level-design.md
|   `-- extraction-review.md
|-- src/egyptian_civil_code_rag/
|   `-- extraction.py
|-- tests/
|-- pyproject.toml
|-- uv.lock
`-- dvc.yaml
```

The package is initialized and locked with `uv`. `pyproject.toml` defines Python and dependencies; `uv.lock` fixes the resolved versions. Start from a fresh clone with these three steps:

```powershell
uv sync --locked
Copy-Item 'PATH_TO_SOURCE\egyption-low.pdf' 'data\raw\egyption-low.pdf'
uv run civil-code-extract
```

The equivalent copy step on macOS/Linux is `cp PATH_TO_SOURCE/egyption-low.pdf data/raw/egyption-low.pdf`.

The command writes `data/processed/egyptian_civil_code.json` and `data/processed/egyptian_civil_code.md`. The original workspace copies of the PDFs and current experiment outputs remain at the top level for review, but are ignored by Git.

## Corpus format

The JSON is one record per article in an array. It contains the handbook fields (`article_number`, `book`, `chapter`, `section`, `topic`, `text_ar`, `text_en`, `is_repealed`, `source_page`, and `citation`) plus identifiers, scope, source-page continuation data, hierarchy, normalized Arabic search text, repeal details, and review flags. These additions preserve provenance and make later indexing safer.

Extraction is not yet approved as a final corpus. The corrected output contains all 1,149 Code article numbers and 56 explicitly repealed records. `docs/extraction-review.md` explains the repaired Article 2 repeal flag, Article 452 label, Article 1022 numbering detection, and 15 Arabic-text gaps that need review before indexing. English coverage is complete for the 1,093 non-repealed records; Arabic coverage is 98.6%. These rates are not transcription accuracy.

## Development

```powershell
uv run ruff check src tests
uv run pytest
uv build
```

`dvc` is an optional uv extra. The source PDF has a DVC pointer at `data/raw/egyption-low.pdf.dvc`, but no shared DVC remote is configured. The PDF itself and DVC cache are not committed to Git, so a fresh clone must supply the PDF until a shared remote is chosen. The extracted JSON and Markdown remain committed review artifacts. After configuring a shared remote, use `uv sync --extra dvc --locked`, `uv run --extra dvc dvc pull`, `uv run --extra dvc dvc repro`, and `uv run --extra dvc dvc push`.

## Design and milestones

- [High-level design](docs/architecture/high-level-design.md): system components, request flow, and deployment path.
- [Low-level design](docs/architecture/low-level-design.md): package boundaries, API contracts, article/chunk/index data contracts, and failure handling.
- [Extraction review](docs/extraction-review.md): method, measured coverage, concrete defects, and corpus acceptance checklist.
- [Visual review checklist](docs/corpus-review-checklist.md): reproducible 20-article sample and all known edge cases for tomorrow's review.
- [Implementation plan](docs/implementation-plan.md): course milestones, acceptance evidence, and release sequence.
- [Contributing](CONTRIBUTING.md): locked setup and checks for changes.

The next milestone is to complete the corpus review, then add a minimal FastAPI `/ask` service and a health endpoint. Evaluation, tracking, tracing, production serving, and optimization follow the handbook's staged requirements.
