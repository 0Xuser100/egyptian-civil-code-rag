# Egyptian Civil Code RAG

An MLOps Project 2 workspace for building a bilingual Arabic and English legal question answering system over article-level Egyptian Civil Code data.

**Current state:** the extraction experiment, corpus review, and end-to-end designs are in place. The `/ask` API, embeddings, vector index, and generation service are the next implementation milestone; this repository does not claim to serve RAG questions yet.

## Project name and structure

Repository name: `egyptian-civil-code-rag`.

```text
.
|-- assets/                  # Extraction report and course handbook PDFs
|-- data/
|   |-- raw/                 # Source PDF from the DVC remote; Git holds only its .dvc pointer
|   `-- processed/           # Article JSON and readable Markdown review
|-- docs/
|   |-- architecture/
|   |   |-- high-level-design.md
|   |   `-- low-level-design.md
|   `-- extraction-review.md
|-- src/egyptian_civil_code_rag/
|   `-- extraction.py
|-- scripts/
|   |-- extract_egyptian_civil_code.py  # Thin entry point to the package
|   `-- profile_corpus.py               # Corpus profiling report
|-- tests/
|-- .dvc/config              # DVC remote settings; no credentials
|-- .env.example             # Placeholder DVC credentials; copy to the Git-ignored .env
|-- pyproject.toml
|-- uv.lock
|-- dvc.yaml                 # Pipeline: PDF -> JSON and Markdown
`-- dvc.lock                 # Checksums of the pipeline inputs and outputs
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

## Data versioning with DVC

`dvc` is an optional uv extra with S3 support. Git stores code and small pointer files; DVC stores the source PDF in a bucket and records the checksums that tie data to each commit.

| Data | Stored in | How to get it |
|---|---|---|
| Source PDF `data/raw/egyption-low.pdf` | DVC remote `storage`; Git holds `data/raw/egyption-low.pdf.dvc` | `dvc pull` |
| Corpus `data/processed/*.json` and `*.md` | Git, as committed review artifacts; `dvc.lock` records their checksums (`cache: false`) | `git clone` or `git checkout` |
| Pipeline | `dvc.yaml` stage `extract_corpus`; `dvc.lock` pins its inputs and outputs | `dvc repro` |

The remote `storage` is an IDrive e2 bucket configured in `.dvc/config`: `s3://egyptian-civil-code-rag-data/egyptian-civil-code-rag`, endpoint `https://s3.us-west-2.idrivee2.com`, region `us-west-2`.

**Credentials.** Copy `.env.example` to `.env` and enter an IDrive access key limited to this bucket. Pass the file with `--env-file .env` on commands that contact the bucket. Git ignores `.env`; never commit keys or paste them into issues or chat. Reviewers should receive their own read-only key.

**Reproduce a commit.** This is the reviewer workflow:

```powershell
uv sync --locked --extra dvc
uv run --extra dvc --env-file .env dvc pull   # download the PDF into data/raw/ and .dvc/cache/
uv run --extra dvc dvc repro                  # rebuild the corpus; "up to date" means it matches dvc.lock
```

**Change the extractor.** Run `uv run --extra dvc dvc repro`, review the `data/processed/` diff, and commit it together with `dvc.lock`. The corpus travels through Git, so no DVC push is needed.

**Replace the source PDF.** Run `uv run --extra dvc dvc add data/raw/egyption-low.pdf` and `uv run --extra dvc dvc repro`. Commit the `.dvc` file, `dvc.lock`, and the corpus, then run `uv run --extra dvc --env-file .env dvc push` before `git push`. If Git receives a pointer whose file never reached the bucket, the change cannot be reproduced.

**Go back to an earlier version.** Run `git checkout <commit>` and then `uv run --extra dvc --env-file .env dvc pull`.

`uv run --extra dvc dvc status` checks the workspace against `dvc.lock`, and `uv run --extra dvc --env-file .env dvc status -c` compares the local cache with the bucket. Without credentials, the restore command above still provides the PDF from `main`.

## Design and milestones

- [High-level design](docs/architecture/high-level-design.md): system components, request flow, and deployment path.
- [Low-level design](docs/architecture/low-level-design.md): package boundaries, API contracts, article/chunk/index data contracts, and failure handling.
- [Extraction review](docs/extraction-review.md): method, measured coverage, concrete defects, and corpus acceptance checklist.
- [Visual review checklist](docs/corpus-review-checklist.md): reproducible 20-article sample and all known edge cases for tomorrow's review.
- [Implementation plan](docs/implementation-plan.md): course milestones, acceptance evidence, and release sequence.
- [Contributing](CONTRIBUTING.md): locked setup and checks for changes.

The next milestone is to complete the corpus review, then add a minimal FastAPI `/ask` service and a health endpoint. Evaluation, tracking, tracing, production serving, and optimization follow the handbook's staged requirements.
