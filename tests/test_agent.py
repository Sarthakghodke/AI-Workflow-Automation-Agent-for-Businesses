from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_sales_summary_execution() -> None:
    payload = {
        "user_id": "u-1",
        "instruction": "Generate this week's sales summary and email it to management.",
        "context": {"week": "2026-W11", "recipients": ["management@company.com"]},
    }
    response = client.post("/execute", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert len(body["plan"]) >= 2
    assert any(step["tool"] == "email_sender" for step in body["plan"])
