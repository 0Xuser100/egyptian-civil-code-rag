import bentoml
from pydantic import BaseModel, Field, field_validator

from rag.pipeline import RAGPipeline


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question must not be empty.")
        return value.strip()


class AskResponse(BaseModel):
    answer: str
    sources: list[str]


@bentoml.service(
    name="egyptian-civil-code-rag",
    traffic={"timeout": 120},
)
class EgyptianCivilCodeRAG:
    def __init__(self) -> None:
        self.pipeline = RAGPipeline()

    @bentoml.api
    async def ask(self, request: AskRequest) -> AskResponse:
        result = self.pipeline.ask(request.question)
        return AskResponse(
            answer=result["answer"],
            sources=result["sources"],
        )

    @bentoml.api
    def ask_stream(self, request: AskRequest):
        yield from self.pipeline.ask_stream(request.question)
