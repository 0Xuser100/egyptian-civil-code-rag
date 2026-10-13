
import asyncio
import json
import math
import time
from pathlib import Path

import faiss
import mlflow
from dotenv import load_dotenv
from evaluate_rag import (
    TEST_CASES,
    build_context,
    generate_answer,
    retrieve_articles,
)
from langfuse import get_client
from openai import AsyncOpenAI
from ragas.embeddings import BaseRagasEmbedding
from ragas.llms import llm_factory
from ragas.metrics.collections import (
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    Faithfulness,
)
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "data/processed/civil_code.faiss"
CHUNKS_PATH = ROOT / "data/processed/rag_chunks.json"
REPORT_PATH = ROOT / "data/processed/ragas_observability_smoke.json"

EMBEDDING_MODEL = "BAAI/bge-m3"
LLM_MODEL = "qwen2.5:3b"
TOP_K = 5


class BGERagasEmbedding(BaseRagasEmbedding):
    """Reuse the project's BGE-M3 embedding model in RAGAS."""

    def __init__(self, model):
        super().__init__()
        self.model = model

    def embed_text(self, text: str, **kwargs) -> list[float]:
        vector = self.model.encode(
            [text],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )[0]
        return vector.tolist()

    async def aembed_text(self, text: str, **kwargs) -> list[float]:
        return await asyncio.to_thread(self.embed_text, text)


async def main():
    # Load Langfuse credentials before creating its client.
    load_dotenv(ROOT / ".env.langfuse", override=True)
    langfuse = get_client()

    # Load the local embedding model and existing FAISS data.
    embedding_model = SentenceTransformer(
        EMBEDDING_MODEL,
        device="cpu",
    )
    embeddings = BGERagasEmbedding(embedding_model)

    index = faiss.read_index(str(INDEX_PATH))
    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))

    # Run a smoke test using one answerable case with a reference.
    case = next(
        (
            item
            for item in TEST_CASES
            if item.get("reference_answer")
            and item.get("expected_articles")
        ),
        None,
    )

    if case is None:
        raise RuntimeError(
            "No test case has both reference_answer and expected_articles."
        )

    question = case["question"]
    reference = case["reference_answer"]

    client = AsyncOpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        timeout=120.0,
    )

    scores = {}
    answer = ""
    retrieved_contexts = []
    generation_latency = 0.0
    retrieval_latency = 0.0
    evaluation_started = time.perf_counter()
    trace_id = None
    langfuse_score_errors = []

    mlflow.set_experiment("egyptian-civil-code-rag")

    try:
        with mlflow.start_run(
            run_name="ragas-langfuse-smoke-test"
        ):
            mlflow.log_params(
                {
                    "embedding_model": EMBEDDING_MODEL,
                    "llm_model": LLM_MODEL,
                    "evaluation_framework": "RAGAS",
                    "evaluation_samples": 1,
                    "vector_store": "FAISS",
                    "top_k": TOP_K,
                    "device": "cpu",
                }
            )

            # Root observation: one complete evaluation request.
            with langfuse.start_as_current_observation(
                as_type="span",
                name="ragas.evaluation",
                input={
                    "question": question,
                    "reference_answer": reference,
                    "evaluation_framework": "RAGAS",
                    "sample_count": 1,
                },
            ) as evaluation_span:

                trace_id = langfuse.get_current_trace_id()

                # Retrieval observation.
                with langfuse.start_as_current_observation(
                    as_type="span",
                    name="rag.retrieval",
                    input={"question": question, "top_k": TOP_K},
                ) as retrieval_span:
                    started = time.perf_counter()

                    results = retrieve_articles(
                        question,
                        embedding_model,
                        index,
                        chunks,
                    )

                    retrieval_latency = (
                        time.perf_counter() - started
                    )

                    retrieved_contexts = [
                        build_context([item])
                        for item in results
                    ]

                    if not retrieved_contexts:
                        raise RuntimeError(
                            "No contexts were retrieved."
                        )

                    context_for_generation = build_context(results)

                    retrieval_span.update(
                        output={
                            "retrieved_context_count": len(results),
                            "retrieved_contexts": retrieved_contexts,
                        },
                        metadata={
                            "latency_seconds": retrieval_latency,
                            "vector_store": "FAISS",
                            "top_k": TOP_K,
                        },
                    )

                # Generation observation.
                with langfuse.start_as_current_observation(
                    as_type="generation",
                    name="rag.generation",
                    model=LLM_MODEL,
                    input={
                        "question": question,
                        "context": context_for_generation,
                    },
                ) as generation_span:
                    answer, generation_latency = generate_answer(
                        question,
                        context_for_generation,
                    )

                    generation_span.update(
                        output={"answer": answer},
                        metadata={
                            "latency_seconds": generation_latency,
                            "model_provider": "Ollama",
                        },
                    )

                # RAGAS scoring.
                with langfuse.start_as_current_observation(
                    as_type="span",
                    name="ragas.scoring",
                    input={
                        "question": question,
                        "metrics": [
                            "faithfulness",
                            "answer_relevancy",
                            "context_precision",
                            "context_recall",
                        ],
                    },
                ) as scoring_span:
                    llm = llm_factory(
                        LLM_MODEL,
                        client=client,
                    )

                    metrics = {
                        "faithfulness": Faithfulness(llm=llm),
                        "answer_relevancy": AnswerRelevancy(
                            llm=llm,
                            embeddings=embeddings,
                        ),
                        "context_precision": ContextPrecision(
                            llm=llm,
                        ),
                        "context_recall": ContextRecall(
                            llm=llm,
                        ),
                    }

                    for name, metric in metrics.items():
                        print(f"Running RAGAS metric: {name} ...")

                        if name == "faithfulness":
                            result = await metric.ascore(
                                user_input=question,
                                response=answer,
                                retrieved_contexts=retrieved_contexts,
                            )
                        elif name == "answer_relevancy":
                            result = await metric.ascore(
                                user_input=question,
                                response=answer,
                            )
                        elif name == "context_precision":
                            result = await metric.ascore(
                                user_input=question,
                                reference=reference,
                                retrieved_contexts=retrieved_contexts,
                            )
                        else:
                            result = await metric.ascore(
                                user_input=question,
                                retrieved_contexts=retrieved_contexts,
                                reference=reference,
                            )

                        score = float(result.value)
                        scores[name] = score
                        print(f"  {name}: {score:.4f}")

                    scoring_span.update(output={"scores": scores})

                # Attach each RAGAS score to this Langfuse trace.
                for name, score in scores.items():
                    if not math.isfinite(score):
                        continue

                    try:
                        score_args = {
                            "name": f"ragas_{name}",
                            "value": score,
                            "data_type": "NUMERIC",
                            "comment": "RAGAS smoke-test metric",
                            "metadata": {
                                "framework": "RAGAS",
                                "model": LLM_MODEL,
                            },
                        }

                        if trace_id:
                            score_args["trace_id"] = trace_id

                        langfuse.create_score(**score_args)

                    except Exception as exc:  # noqa: BLE001 — score logging failure should not abort evaluation
                        langfuse_score_errors.append(
                            {"metric": name, "error": str(exc)}
                        )
                        print(
                            f"Warning: Langfuse score failed for "
                            f"{name}: {exc}"
                        )

                duration = time.perf_counter() - evaluation_started

                evaluation_span.update(
                    output={
                        "answer": answer,
                        "scores": scores,
                    },
                    metadata={
                        "retrieval_latency_seconds": retrieval_latency,
                        "generation_latency_seconds": generation_latency,
                        "evaluation_duration_seconds": duration,
                    },
                )

                # Log numeric metrics to MLflow.
                for name, score in scores.items():
                    if math.isfinite(score):
                        mlflow.log_metric(name, score)

                mlflow.log_metric(
                    "retrieval_latency_seconds",
                    retrieval_latency,
                )
                mlflow.log_metric(
                    "generation_latency_seconds",
                    generation_latency,
                )
                mlflow.log_metric(
                    "evaluation_duration_seconds",
                    duration,
                )

                report = {
                    "question": question,
                    "reference_answer": reference,
                    "answer": answer,
                    "retrieved_contexts": retrieved_contexts,
                    "scores": scores,
                    "trace_id": trace_id,
                    "latency_seconds": {
                        "retrieval": retrieval_latency,
                        "generation": generation_latency,
                        "total": duration,
                    },
                    "langfuse_score_errors": langfuse_score_errors,
                }

                REPORT_PATH.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )
                REPORT_PATH.write_text(
                    json.dumps(
                        report,
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )

                mlflow.log_artifact(str(REPORT_PATH))

                print("\nRAGAS smoke test completed.")
                print(f"Langfuse trace ID: {trace_id}")
                print(f"Report: {REPORT_PATH}")

                if langfuse_score_errors:
                    print(
                        "Warning: some Langfuse scores were not recorded. "
                        "Check the warnings above."
                    )
                else:
                    print("Langfuse score submission completed.")

    finally:
        await client.close()
        try:
            langfuse.flush()
        except Exception as exc:  # noqa: BLE001 — telemetry flush failure should not mask evaluation results
            print(f"Warning: Langfuse flush failed: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
