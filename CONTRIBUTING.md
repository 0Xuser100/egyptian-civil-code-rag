# Contributing

Use Python 3.13 and `uv sync --locked` to install the package and development tools. Work on a feature or experiment branch and open a pull request when the change is ready for review.

For extraction changes, supply `data/raw/egyption-low.pdf` locally or pull it from the DVC remote as described in the README. Run `uv run --extra dvc --locked dvc repro`, inspect the JSON and Markdown diff, commit it with `dvc.lock`, and explain any changes to article boundaries, hierarchy, repeal flags, or missing-language records. Never fill a source gap with generated legal text.

Before submitting, run:

```sh
uv run --locked ruff check src tests scripts
uv run --locked pytest -q
uv build
```

Commit `pyproject.toml` and `uv.lock` together when changing dependencies. Keep PDFs, caches, credentials, and local environments out of Git. The processed corpus is committed for review; DVC records its checksums with `cache: false`. DVC remote credentials belong only in the Git-ignored `.env`. When the source PDF changes, run `dvc push` before `git push` so every committed pointer can be pulled.

The architecture documents describe future milestones. Implement one reviewed milestone at a time and update the README when functionality becomes available. See `docs/implementation-plan.md` for the delivery sequence and acceptance evidence.
