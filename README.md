# Egyptian Civil Code RAG

A simple baseline for the Egyptian Civil Code extraction experiment and the upcoming RAG project.

## Structure

```text
assets/
  egyptian-civil-code-extraction-report.pdf
  The-MLOps-Practitioner-Handbook-3-tracks.pdf
data/
  raw/
    egyption-low.pdf
  processed/
    egyptian_civil_code.json
    egyptian_civil_code.md
scripts/
  extract_egyptian_civil_code.py
.python-version
pyproject.toml
uv.lock
```

`assets/` contains the extraction guidance and course requirements. `data/raw/` contains the original bilingual PDF. `data/processed/` contains the extracted article records and readable review output. `scripts/` contains the standalone extractor.

## Run extraction

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and run from the repository root:

```sh
uv sync --locked
uv run --locked python scripts/extract_egyptian_civil_code.py
```

The script uses PyMuPDF table detection with `strategy="lines"` and extracts text from each cell's bounding box. It writes the JSON and Markdown under `data/processed/`. To select other paths:

```sh
uv run --locked python scripts/extract_egyptian_civil_code.py data/raw/egyption-low.pdf --json data/processed/egyptian_civil_code.json --markdown data/processed/egyptian_civil_code.md
```

## Current extraction

The output includes 1,149 Civil Code article records and 56 explicitly repealed articles. All Code article numbers and English texts are present. Fifteen records lack Arabic text and retain review flags; these require source comparison before indexing. Coverage is not transcription accuracy. The two issuing-law articles above the table on PDF page 1 are outside this Code-only export.

This baseline contains the input, reference assets, script, and outputs for review. The RAG API, embeddings, and deployment are future work. Create the next feature branch from this updated `main` and submit it as a pull request.
