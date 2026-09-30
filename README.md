# Egyptian Civil Code RAG

An MLOps Project 2 workspace for building a bilingual Arabic and English legal question answering system over article-level Egyptian Civil Code data.

**Current state:** the extraction experiment, corpus review, and end-to-end designs are in place. The `/ask` API, embeddings, vector index, and generation service are the next implementation milestone; this repository does not claim to serve RAG questions yet.

## Project name and structure

Repository name: `egyptian-civil-code-rag`.

```text
.
|-- assets/                  # Extraction report and course handbook PDFs
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
|-- scripts/
|   `-- extract_egyptian_civil_code.py  # Thin entry point to the package
|-- tests/
|-- pyproject.toml
|-- uv.lock
`-- dvc.yaml
```

The package is initialized and locked with `uv`. `pyproject.toml` defines Python and dependencies; `uv.lock` fixes the resolved versions. Start from a fresh clone with these three steps:

```powershell
uv sync --locked
git restore --source origin/main --worktree -- data/raw/egyption-low.pdf
uv run civil-code-extract
```

The source restore command works on Windows, macOS, and Linux. Alternatively, supply your own copy at `data/raw/egyption-low.pdf`.

The command writes `data/processed/egyptian_civil_code.json` and `data/processed/egyptian_civil_code.md`. Reference PDFs live in `assets/`; there are no top-level duplicate artifacts. `uv run --locked python scripts/extract_egyptian_civil_code.py` invokes the same packaged implementation as `civil-code-extract`.

## Corpus format

The JSON is one record per article in an array. It contains the handbook fields (`article_number`, `book`, `chapter`, `section`, `topic`, `text_ar`, `text_en`, `is_repealed`, `source_page`, and `citation`) plus identifiers, scope, source-page continuation data, hierarchy, normalized Arabic search text, repeal details, and review flags. These additions preserve provenance and make later indexing safer.

Extraction is not yet approved as a final corpus. The regenerated output contains all 1,149 Code article numbers and 56 explicitly repealed records. English text is present for all 1,093 non-repealed records; Arabic text is present for 1,092 (99.91%), with Article 1022 still flagged for review. These are coverage rates, not transcription accuracy. See `docs/extraction-review.md`, `docs/extraction-accuracy-review.md`, and `docs/corpus-review-checklist.md` before indexing.

## Development

```powershell
uv run ruff check src tests scripts
uv run pytest
uv build
```

`dvc` is an optional uv extra with S3 support. This branch versions the source with `data/raw/egyption-low.pdf.dvc` and excludes the PDF and cache from Git. The default DVC remote, `storage`, is an IDrive e2 bucket configured in `.dvc/config`. The extracted JSON and Markdown remain committed review artifacts; `dvc.lock` records their checksums. To use the remote, copy `.env.example` to `.env` and enter an IDrive access key for the bucket, then run `uv sync --extra dvc --locked`, `uv run --extra dvc --env-file .env dvc pull`, `uv run --extra dvc dvc repro`, and `uv run --extra dvc --env-file .env dvc push`. Without credentials, the restore command above still provides the PDF from `main`.

## Design and milestones

- [High-level design](docs/architecture/high-level-design.md): system components, request flow, and deployment path.
- [Low-level design](docs/architecture/low-level-design.md): package boundaries, API contracts, article/chunk/index data contracts, and failure handling.
- [Extraction review](docs/extraction-review.md): method, measured coverage, concrete defects, and corpus acceptance checklist.
- [Visual review checklist](docs/corpus-review-checklist.md): reproducible 20-article sample and all known edge cases for tomorrow's review.
- [Implementation plan](docs/implementation-plan.md): course milestones, acceptance evidence, and release sequence.
- [Contributing](CONTRIBUTING.md): locked setup and checks for changes.

The next milestone is to complete the corpus review, then add a minimal FastAPI `/ask` service and a health endpoint. Evaluation, tracking, tracing, production serving, and optimization follow the handbook's staged requirements.
