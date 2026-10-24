from __future__ import annotations

from fastapi.testclient import TestClient

from api.gateway import create_app, gateway_reason_codes


def test_gateway_generates_correlation_id_when_header_is_missing():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    correlation_id = response.headers["X-Correlation-ID"]
    assert correlation_id
    assert len(correlation_id) == 36


def test_gateway_preserves_supplied_correlation_id():
    client = TestClient(create_app())

    response = client.get(
        "/health",
        headers={"X-Correlation-ID": "trace-day83-001"},
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == "trace-day83-001"


def test_reason_codes_body_and_response_header_match():
    client = TestClient(create_app())

    response = client.post(
        "/reason-codes",
        json={
            "evidence": {},
            "correlation_id": "body-trace-83",
        },
    )

    assert response.status_code == 200
    assert response.json()["correlation_id"] == "body-trace-83"
    assert response.headers["X-Correlation-ID"] == "body-trace-83"


def test_reason_codes_header_takes_precedence_over_body():
    client = TestClient(create_app())

    response = client.post(
        "/reason-codes",
        headers={"X-Correlation-ID": "header-trace-83"},
        json={
            "evidence": {},
            "correlation_id": "body-trace-83",
        },
    )

    assert response.status_code == 200
    assert response.json()["correlation_id"] == "header-trace-83"
    assert response.headers["X-Correlation-ID"] == "header-trace-83"


def test_invalid_correlation_header_is_rejected():
    client = TestClient(create_app())

    response = client.get(
        "/health",
        headers={"X-Correlation-ID": "invalid trace id"},
    )

    assert response.status_code == 400


def test_oversized_correlation_header_is_rejected():
    client = TestClient(create_app())

    response = client.get(
        "/health",
        headers={"X-Correlation-ID": "x" * 129},
    )

    assert response.status_code == 400


def test_invalid_body_correlation_id_is_rejected():
    client = TestClient(create_app())

    response = client.post(
        "/reason-codes",
        json={
            "evidence": {},
            "correlation_id": "invalid trace id",
        },
    )

    assert response.status_code == 422


def test_direct_reason_code_call_generates_correlation_id():
    result = gateway_reason_codes({"evidence": {}})

    assert isinstance(result["correlation_id"], str)
    assert len(result["correlation_id"]) == 36
