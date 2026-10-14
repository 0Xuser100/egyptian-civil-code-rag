
import time
from contextlib import asynccontextmanager
from pathlib import Path

import mlflow
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from langfuse import get_client
from pydantic import BaseModel, Field, field_validator

from rag.config import MLFLOW_EXPERIMENT, TOP_K
from rag.generator import generate_answer
from rag.pipeline import RAGPipeline, build_context
from rag.retriever import retrieve_articles

# Load Langfuse environment variables before creating the client.
ENV_FILE = Path(__file__).resolve().parents[2] / ".env.langfuse"
load_dotenv(ENV_FILE, override=False)

pipeline: RAGPipeline | None = None
langfuse = get_client()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline

    pipeline = RAGPipeline()

    try:
        yield
    finally:
        pipeline = None
        langfuse.flush()


app = FastAPI(
    title="Egyptian Civil Code RAG API",
    description="Production-style RAG API for the Egyptian Civil Code.",
    version="1.0.0",
    lifespan=lifespan,
)


class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Question about the Egyptian Civil Code.",
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Question cannot be empty.")

        return value


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[str]


@app.get("/health")
def health() -> dict[str, int | str]:
    if pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline is not ready.",
        )

    return {
        "status": "healthy",
        "documents_indexed": len(pipeline.chunks),
    }


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    if pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline is not ready.",
        )

    start_time = time.perf_counter()
    mlflow.set_experiment(MLFLOW_EXPERIMENT)

    with langfuse.start_as_current_observation(
        as_type="span",
        name="rag.ask",
        input={"question": request.question},
    ) as root:
        try:
            with mlflow.start_run(run_name="api-query"):
                mlflow.log_param("question", request.question)

                # Retrieval span
                with langfuse.start_as_current_observation(
                    as_type="span",
                    name="rag.retrieval",
                    input={"question": request.question},
                ) as retrieval_span:
                    results = retrieve_articles(
                        question=request.question,
                        model=pipeline.embedding_model,
                        index=pipeline.index,
                        chunks=pipeline.chunks,
                        top_k=TOP_K,
                    )

                    retrieval_span.update(
                        output={
                            "retrieved_count": len(results),
                            "results": [
                                {
                                    "article_number": item["article_number"],
                                    "chunk_id": item["id"],
                                    "score": item["score"],
                                }
                                for item in results
                            ],
                        },
                    )

                context = build_context(results)

                # Generation span
                with langfuse.start_as_current_observation(
                    as_type="generation",
                    name="rag.generation",
                    input={
                        "question": request.question,
                        "context": context,
                    },
                ) as generation:
                    answer = generate_answer(
                        question=request.question,
                        context=context,
                    )

                    generation.update(output=answer)

                sources = [
                    f"المادة {result['article_number']}"
                    for result in results
                ]

                response = AskResponse(
                    question=request.question,
                    answer=answer,
                    sources=sources,
                )

                latency = time.perf_counter() - start_time

                # MLflow metrics
                mlflow.log_metric(
                    "total_latency_seconds",
                    latency,
                )
                mlflow.log_metric(
                    "retrieved_sources_count",
                    len(sources),
                )

                if sources:
                    mlflow.log_param("top_article", sources[0])

                # Root observation output
                root.update(
                    output={
                        "answer": response.answer,
                        "sources": response.sources,
                    },
                    metadata={
                        "latency_seconds": latency,
                        "retrieved_sources_count": len(sources),
                    },
                )

                return response

        except HTTPException:
            root.update(
                level="ERROR",
                status_message="HTTP error while processing request",
            )
            raise

        except Exception as exc:
            root.update(
                level="ERROR",
                status_message="Failed to process RAG request",
            )
            print(f"RAG ERROR: {exc!r}")

            raise HTTPException(
                status_code=500,
                detail="Failed to process the question.",
            ) from exc
