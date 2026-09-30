# Implementation Plan

The current branch implements reproducible extraction and records the intended RAG architecture. This plan turns the handbook's Final Project 2 into reviewable increments. It does not mark planned services as implemented.

| Increment | Deliverables | Acceptance evidence |
|---|---|---|
| 1. Extraction experiment (current) | Locked uv package, PyMuPDF cell extraction, JSON/Markdown, DVC pipeline with the shared IDrive e2 remote, focused tests, HLD/LLD | All 1,149 Code IDs; correct explicit repeal ranges; known language gaps preserved; lint/tests/package build pass |
| 2. Corpus approval | 20 random visual comparisons; review the 14 recovered Arabic articles, the restored lam-alef text, the Article 1022 gap, and hierarchy; source provenance | Signed review checklist and versioned reviewed corpus; unresolved gaps have an explicit exclusion or handling policy |
| 3. Retrieval baseline | Validated article schema, language-specific article/paragraph chunks, multilingual embeddings, pgvector index CLI | Deterministic IDs; reproducible index; retrieval cases in both languages; model/index mismatch blocks readiness |
| 4. Query service | FastAPI `POST /ask`, `GET /health`, generation adapter, citations, abstention, bounded timeouts | Empty question returns 422; answers cite retrieved articles; known unsupported questions abstain; Docker/Compose smoke check |
| 5. Experiments | 50+ reviewed bilingual questions; fixed 20-question CI subset; separate human-labeled judge calibration set; five MLflow runs | RAGAS report with language breakdown and selected configuration; stable CI faithfulness at least 0.75 |
| 6. Monitoring and safety | Langfuse spans and linked evaluation scores, PII redaction, injection handling, drift and cost metrics, Grafana | Every request traceable without sensitive logs; faithfulness alert below 0.80; real Arabic and injection checks |
| 7. Serving and optimization | BentoML RAG wrapper, vLLM generation, streaming, AWQ 4-bit, re-ranker distillation, Locust | 50 concurrent users measured; optimization faithfulness loss at most 0.03 on the same cases |
| 8. Release | Image publishing, secrets and DVC credentials in deployment platform, canary, rollback runbook | Approved immutable image and corpus/model versions promoted together; failed gates roll traffic back |

## Configuration to introduce with the API milestone

Use environment-backed settings for `DATABASE_URL`, LLM credentials/model, embedding model/revision, active corpus version, retrieval candidate count, context budget, timeouts, and tracing credentials. `.env.example` currently holds only the DVC remote credentials; add other placeholders only when those settings exist in code. Avoid installing or creating service scaffolding before implementing the relevant increment.

Local Compose will expose the API on port 8000 and pgvector on port 5432 for development. In deployment, keep the database private, inject secrets at runtime, and expose only the HTTPS ingress. The first release uses an external LLM API; the later vLLM service needs a measured GPU capacity plan.

## Release sequence

1. CI validates code, corpus contract, evaluation gate, and image build.
2. Publish an image tagged with the Git revision and record the approved corpus/model manifest.
3. Run database migrations and load a new immutable index version outside the HTTP process.
4. Verify corpus/embedding compatibility and readiness before routing canary traffic.
5. Measure failures, latency, and sampled evaluation against the release baseline; promote or roll back.
6. Keep the previous image and index available until the release is accepted; back up the database and shared DVC storage.

The extraction branch can be reviewed without deploying services. The private GitHub repository is published. Main contains the simple structured dataset, assets, standalone extractor, and processed outputs; this branch adds the packaged experiment, DVC workflow, tests, CI, and architecture documents.
