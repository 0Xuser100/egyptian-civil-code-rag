# Low-Level Design

**Status:** implementation blueprint. Only article extraction is implemented today. Module paths and API schemas below describe the next increments, not shipped functionality.

## Package boundaries

Keep one Python package and make ownership explicit. Add modules when each increment is implemented; do not pre-create empty modules just to match the diagram.

```text
src/egyptian_civil_code_rag/
|-- extraction.py            # PDF table/cell extraction and current CLI
|-- corpus/
|   |-- schema.py             # Article and chunk contracts
|   |-- validation.py         # Invariants and review flags
|   |-- chunking.py           # Article/paragraph chunk creation
|   `-- indexing.py           # Embedding and index build orchestration
|-- retrieval/
|   |-- repository.py         # Vector query and metadata filters
|   `-- service.py            # Retrieve, de-duplicate, and rank article evidence
|-- generation/
|   |-- provider.py           # LLM call boundary
|   `-- prompting.py          # Evidence-only prompt construction
|-- api/
|   |-- app.py                # FastAPI application and lifespan
|   |-- schemas.py            # Request/response validation
|   `-- routes.py             # /ask and /health
|-- evaluation/
|   |-- questions.py          # Versioned bilingual evaluation cases
|   `-- run.py                # RAGAS run and MLflow logging
`-- settings.py               # Environment-backed configuration
```

This is a modular monolith. Routers own HTTP parsing only; services own use cases; repository adapters own database operations; schema types own the data contract. Keep provider calls and vector storage behind small interfaces so evaluation can replace them without mocking HTTP routes.

## Article contract

The extractor exports a JSON array with one record for each article number. The required handbook fields are:

| Field | Type | Rule |
|---|---|---|
| `article_number` | integer | Stable legal article identifier; never a parsed string |
| `book`, `chapter`, `section`, `topic` | string or null | Hierarchy at the article location |
| `text_ar`, `text_en` | string | Preserve source text; gaps are explicit review flags |
| `is_repealed` | boolean | Keep the article record and mark repeal status |
| `source_page` | integer or null | First PDF page where the record appears |
| `citation` | string | Human-readable article citation |

The current extractor extends this with `id`, `scope`, `arabic_norm`, `source_pages`, `repealed_range`, `repeal_note`, `hierarchy_ar`, `hierarchy_en`, and `flags`. Do not remove these fields without first migrating the ingestion and review artifacts.

Use `book` for actual Book headings. Preserve Part headings separately in `hierarchy_en` and `hierarchy_ar`; the handbook example's "Obligations or Personal Rights" is a Part in this PDF. The current export has `scope=code` only. Two Arabic-only promulgating-law provisions above the table on page 1 are excluded; adding them requires `scope=issuing_law` so their numbers do not collide with Code Articles 1 and 2.

## Chunk contract

```json
{
  "chunk_id": "code-0147-en-000",
  "article_number": 147,
  "language": "en",
  "text": "The contract makes the law of the parties...",
  "citation": "Egyptian Civil Code, Article 147",
  "is_repealed": false,
  "hierarchy": {"book": "...", "chapter": "...", "section": "...", "topic": "..."},
  "corpus_version": "<source-and-extractor-fingerprint>"
}
```

Create one language-specific chunk per article by default. If an article is too long for the configured model context, split only at paragraph boundaries; repeat `article_number`, `citation`, language, repeal state, and hierarchy on every child chunk. Never merge two article numbers into one chunk. The same article in Arabic and English shares an article identifier but keeps separate text and embeddings. Retrieval groups results by article before prompt construction.

## API contract

### `POST /ask`

Request:

```json
{
  "question": "What conditions make a contract binding?",
  "language": "en"
}
```

`question` is required, trimmed, and non-empty; malformed or empty requests return HTTP 422. `language` is optional (`ar` or `en`); if absent, the service detects it. Add only validated hierarchy filters when needed; clients cannot provide SQL or raw vector-store expressions.

Response:

```json
{
  "answer": "...",
  "sources": [
    {"article_number": 147, "citation": "Egyptian Civil Code, Article 147"}
  ],
  "answer_language": "en"
}
```

Sources are article citations, not page numbers or internal chunk IDs. If no retrieved context clears the configured relevance threshold, return a short abstention and an empty `sources` array.

### `GET /health`

Return HTTP 200 only when the API can reach its required dependencies and the active corpus is loaded:

```json
{"status": "healthy", "documents_indexed": 1149}
```

Use a separate readiness check if deployment must distinguish a live process from a usable vector index.

## Query sequence

1. FastAPI validates `AskRequest` and assigns a request/trace ID.
2. `QueryService` normalizes only the search representation; the original question remains unchanged for the response and trace policy.
3. `EmbeddingAdapter` embeds the query with the same model/version used for the active index.
4. `VectorRepository` performs cosine search and applies `scope=code` by default. It returns a configurable candidate set with article metadata.
5. `RetrievalService` de-duplicates language/paragraph hits by article, preserves both matching language text and repeal metadata, and enforces a maximum context budget.
6. `PromptBuilder` supplies only retrieved provisions, their citations, the response language, and an instruction to abstain when unsupported.
7. `GenerationAdapter` calls the configured LLM. The service attaches citations from retrieved metadata rather than trusting citation strings invented by the model.
8. The response schema is validated, then Langfuse receives redacted trace spans and latency/token metadata.

## Storage model

Use PostgreSQL with the `vector` extension for the first deployment. Keep one row per language-specific chunk:

| Column | Purpose |
|---|---|
| `chunk_id` | Deterministic primary key from corpus version/article/language/part |
| `corpus_version` | Source checksum + extractor/schema version |
| `article_number`, `language`, `chunk_index` | Stable retrieval identity |
| `text` | Exact chunk text used for retrieval/generation |
| `embedding` | Vector with the dimension fixed by the chosen embedding model |
| `metadata` | Citation, hierarchy, repeal status, and source-page list |

Create a unique constraint on `(corpus_version, article_number, language, chunk_index)`, a B-tree index on common filters, and an HNSW cosine index after measuring corpus size and query latency. Keep the existing article JSON as the source of truth; the vector table is rebuildable. Do not change embedding dimensions or model silently within one corpus version.

## Extraction and corpus validation

The current parser uses `page.find_tables(strategy="lines")` and extracts each cell with `page.get_text("text", clip=cell)`. It classifies language per cell and maintains independent English and Arabic article cursors so continuation rows do not shift the bilingual columns. It normalizes Unicode, restores Arabic-Indic digit runs when the PDF text layer reverses them, captures headings, and records page provenance.

Before indexing, validate:

- required handbook fields exist with the declared types;
- `(scope, article_number)` is unique and article IDs are represented or explicitly explained;
- missing language text is flagged and reviewed, not silently accepted;
- repeal status comes only from explicit source repeal statements/ranges;
- citations match article numbers and source page references exist;
- Arabic text is spot-checked visually, including randomized articles and known extraction edge cases.

The printed English label `Article1022` has no space. The corrected parser recognizes it on PDF page 147 and includes its continuation on page 148, eliminating the false numbering gap. Its Arabic cell is blank; Arabic paragraphs under Article 1021 must not be reassigned without legal review. There are 15 non-repealed records without extracted Arabic text. Keep those records flagged and complete the handbook's 20-article visual spot-check before approving the corpus for embeddings. Coverage measures do not establish transcription accuracy.

## Experiment and evaluation contracts

- MLflow parameters: `chunk_size`, `overlap`, `embedding_model`, corpus version, generation model, and retrieval `top_k`.
- MLflow metrics/artifacts: RAGAS faithfulness, context precision/recall, answer relevance, the evaluation question-set version, and results by language.
- Compare at least five chunking/embedding configurations before registering the chosen configuration.
- Version one reviewed set of at least 50 bilingual questions. Reserve a fixed 20-question subset for the CI faithfulness gate (`0.75` minimum), report at least 30 cases for the Module 5 scorecard, and use the full set for monitoring evaluation. Keep a separate 20-case human-labeled judge calibration set. Do not use evaluation questions as prompt examples.
- Langfuse traces each `/ask` request with retrieval and generation spans, model/index versions, latency, token counts, cost, and error state. Attach offline RAGAS scores through the corresponding trace IDs; a synchronous production request need not wait for a judge call. Redact secrets and PII before recording traces.
- Track embedding cosine-distribution drift against a versioned reference sample. Expose request/error/latency counters, hourly token cost, and aggregate faithfulness to Grafana; alert when measured faithfulness falls below `0.80`. Record judge model and sample count so metric changes are interpretable.

## Query safety and deployment acceptance

Treat the question and retrieved documents as untrusted input. Apply request-size limits, PII redaction for logs, and a prompt-injection check before generation; keep source text delimited and prohibit document instructions from changing system behavior. Validate output citations against the retrieved article set and test Arabic questions and injection attempts before release. A rejected unsafe request returns a stable 400 response; record the rejection reason without retaining sensitive text.

The later BentoML service wraps retrieval and generation; vLLM supplies generation with streaming through `/ask`. Compare AWQ 4-bit quantization and re-ranker distillation to the registered baseline on the same question set; accept a faithfulness drop of at most `0.03`. Use Locust with 50 concurrent users and record latency percentiles, throughput, failure rate, and GPU/CPU utilization. Define release latency limits from measured baseline results rather than inventing targets.

Promote the image, corpus fingerprint, embedding model, and generation model as one release configuration. Send a small configured traffic share to a canary; promote only after readiness, error rate, latency, and evaluated faithfulness satisfy the release criteria. Roll back traffic to the previous configuration if a gate fails. Preserve the previous index until the release is accepted.

## Runtime and release boundaries

- Local: `uv sync --locked`; Docker Compose will run API and pgvector once the API slice exists.
- CI: lockfile install, Ruff, pytest, corpus schema checks, package/container build, and later the RAGAS gate.
- Release: build an immutable image, tag it with the code revision, and record the corpus fingerprint and model identifiers. Re-index and validate before switching the active corpus.
- Production: API container behind HTTPS ingress, managed PostgreSQL/pgvector, durable backups, and secrets supplied by the deployment platform. The LLM provider is external in the first release. The later offline course stage uses BentoML and vLLM/AWQ.

## Error behavior

| Failure | Behavior |
|---|---|
| Invalid/empty question | HTTP 422 with a stable validation response |
| Vector store unavailable | Health is degraded; `/ask` returns a retriable 503 |
| Embedding or generation provider timeout | Bounded timeout and 503; never emit a fabricated fallback answer |
| No relevant legal evidence | 200 with abstention text and no sources |
| Retrieved article is marked repealed | Include repeal status in the context and answer; do not drop the source silently |
| Corpus version/model mismatch | Refuse readiness rather than query vectors produced by another model |
