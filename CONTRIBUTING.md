# Contributing

This repository turns the Egyptian Civil Code PDF into an article-level corpus for a bilingual RAG system. Code and the processed corpus live in Git; the source PDF lives in a DVC remote. Follow this guide so that two people can work in the same repository without overwriting each other and every commit stays reproducible.

## First-time setup

1. Ask the repository owner to add you as a GitHub collaborator and to create your own IDrive e2 access key for the bucket `egyptian-civil-code-rag-data`. Keys are personal: never share one or use someone else's. The key arrives privately, never in a group chat, issue, or commit.
2. Install Python 3.13 and [uv](https://docs.astral.sh/uv/), then clone and install the locked environment:

   ```powershell
   git clone https://github.com/0Xuser100/egyptian-civil-code-rag.git
   cd egyptian-civil-code-rag
   uv sync --locked --extra dvc
   ```

3. Copy `.env.example` to `.env` and enter your key. Git ignores `.env`.

   ```powershell
   Copy-Item .env.example .env
   ```

4. Download the source PDF and confirm that the workspace matches the pipeline:

   ```powershell
   uv run --extra dvc --env-file .env dvc pull
   uv run --extra dvc dvc status    # expect "Data and pipelines are up to date."
   ```

The "Data versioning with DVC" section of the README explains where each file is stored.

## Branches

- `main` is the simple baseline. It changes only through reviewed pull requests.
- `project2/rag-foundation` is the integration branch for Project 2. Open pull requests into it.
- Every change gets its own short-lived branch, for example `fix/article-1022` or `feat/chunking`.

Never commit to the same branch as another contributor at the same time. Start each change from the latest integration branch:

```powershell
git switch project2/rag-foundation
git pull
uv run --extra dvc --env-file .env dvc pull
git switch -c fix/short-description
```

If the integration branch moves while you work, run `git pull origin project2/rag-foundation` on your branch, then `uv run --extra dvc dvc repro`. When both branches changed the corpus, resolve conflicts in the code first, then regenerate `data/processed/` and `dvc.lock` with `dvc repro` instead of editing them by hand.

## Making a change

### Code or extraction

1. Edit `src/egyptian_civil_code_rag/` and add or update tests in `tests/`.
2. Rebuild the corpus with `uv run --extra dvc dvc repro`.
3. Inspect `git diff data/processed/` and explain any change to article boundaries, hierarchy, repeal flags, or missing-language records in the pull request.
4. Commit the code, tests, `data/processed/`, and `dvc.lock` together. The corpus travels through Git (`cache: false`), so no `dvc push` is needed.

### Source PDF

1. Place the new file at `data/raw/egyption-low.pdf`.
2. Run `uv run --extra dvc dvc add data/raw/egyption-low.pdf`, then `uv run --extra dvc dvc repro`.
3. Update the source SHA-256 in `docs/review-provenance.md` and `docs/corpus-review-checklist.md`.
4. Commit `data/raw/egyption-low.pdf.dvc`, `dvc.lock`, `data/processed/`, and the docs.
5. Run `uv run --extra dvc --env-file .env dvc push`, and only then `git push`. A pushed pointer whose file never reached the bucket cannot be pulled by anyone.

### Dependencies

Change dependencies with `uv add`, or edit `pyproject.toml` and run `uv lock`. Commit `pyproject.toml` and `uv.lock` together. Both are pipeline inputs, so run `dvc repro` and commit the updated `dvc.lock` as well.

## Before you push

Run these checks. All must pass; CI runs the first three on every push and pull request.

```powershell
uv run --locked ruff check src tests scripts
uv run --locked pytest -q
uv build
uv run --extra dvc dvc status
```

Stage files by name and check `git status` before each commit.

## Pull requests

- Keep one topic per pull request and open it into `project2/rag-foundation`.
- Fill in the template: the change, the checks you ran and their results, and the data impact. For extraction changes, report article counts, language gaps, repeal changes, and source-page comparisons.
- Merge only after CI is green and the other contributor has reviewed the change.

## Data and legal text

- Never fill a source gap with generated or AI-written legal text. Article 1022 stays flagged until a legal review decides how to handle it.
- Keep repealed articles as flagged records; do not delete them.
- Do not move text between articles without checking the source PDF page and recording the decision in `docs/`.
- Record visual review results in `docs/corpus-review-checklist.md` and `docs/extraction-accuracy-review.md`.

## Secrets and files kept out of Git

Never commit `.env`, access-key files downloaded from IDrive, `.dvc/config.local`, the PDF in `data/raw/`, `.dvc/cache/`, `.venv/`, or build output. `.gitignore` already excludes them.

If a key is exposed, for example pasted into a chat or committed, tell the repository owner at once. The owner revokes it in IDrive and issues a new one. Deleting the commit or message is not enough, because Git history and chat logs keep copies.

## Documentation

The architecture documents describe future milestones. Implement one reviewed milestone at a time and update the README when functionality becomes available. See `docs/implementation-plan.md` for the delivery sequence and acceptance evidence.
