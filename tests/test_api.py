from fastapi.testclient import TestClient

from rag import api


def test_empty_question_returns_422() -> None:
    client = TestClient(api.app)

    response = client.post(
        "/ask",
        json={"question": "   "},
    )

    assert response.status_code == 422


def test_health_returns_healthy(monkeypatch) -> None:
    class FakePipeline:
        def __init__(self) -> None:
            self.chunks = [1, 2, 3]

    monkeypatch.setattr(
        api,
        "pipeline",
        FakePipeline(),
    )

    client = TestClient(api.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "documents_indexed": 3,
    }

    client = TestClient(api.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "documents_indexed": 3,
    }