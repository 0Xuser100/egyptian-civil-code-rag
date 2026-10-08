import time
from contextlib import asynccontextmanager

import mlflow
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from rag.config import MLFLOW_EXPERIMENT
from rag.pipeline import RAGPipeline

pipeline: RAGPipeline | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline

    pipeline = RAGPipeline()

    yield

    pipeline = None


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

    try:
        with mlflow.start_run(run_name="api-query"):
            mlflow.log_param("question", request.question)

            result = pipeline.ask(request.question)

            latency = time.perf_counter() - start_time

            mlflow.log_metric(
                "total_latency_seconds",
                latency,
            )

            mlflow.log_metric(
                "retrieved_sources_count",
                len(result["sources"]),
            )

            if result["sources"]:
                mlflow.log_param(
                    "top_article",
                    result["sources"][0],
                )

            response = AskResponse(
                question=result["question"],
                answer=result["answer"],
                sources=result["sources"],
            )

            return response

    except HTTPException:
        raise

    except Exception as exc:
        print(f"RAG ERROR: {exc!r}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process the question.",
        ) from exc