import re

from fastapi.testclient import TestClient

from api.gateway import create_app


def make_payload():
    return {
        "authorization_result": {
            "decision": "ALLOW",
            "reason": "Hypothetical policy allow",
        },
        "lease_id": "lease-1",
        "agent_id": "agent-1",
        "capability": "read_report",
        "resource": "reports/weekly.csv",
    }


def test_day89_unavailable_registry_has_explicit_safe_contract():
    client = TestClient(create_app())

    response = client.post(
        "/counterfactual-capability",
        json=make_payload(),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["available"] is False
    assert body["decision"] == "UNAVAILABLE"
    assert body["allowed"] is False
    assert body["reason_code"] == "LEASE_REGISTRY_UNAVAILABLE"
    assert body["evaluation_type"] == "COUNTERFACTUAL"
    assert body["executed"] is False
    assert body["live_authorization"] is False


def test_day89_generated_correlation_id_matches_response_header():
    client = TestClient(create_app())

    response = client.post(
        "/counterfactual-capability",
        json=make_payload(),
    )

    assert response.status_code == 200
    body_id = response.json()["correlation_id"]
    header_id = response.headers["X-Correlation-ID"]

    assert isinstance(body_id, str)
    assert re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", body_id)
    assert header_id == body_id


def test_day89_valid_correlation_id_is_preserved():
    client = TestClient(create_app())

    response = client.post(
        "/counterfactual-capability",
        headers={"X-Correlation-ID": "day89.trace-001"},
        json=make_payload(),
    )

    assert response.status_code == 200
    assert response.json()["correlation_id"] == "day89.trace-001"
    assert response.headers["X-Correlation-ID"] == "day89.trace-001"


def test_day89_invalid_correlation_id_is_rejected():
    client = TestClient(create_app())

    response = client.post(
        "/counterfactual-capability",
        headers={"X-Correlation-ID": "invalid trace id"},
        json=make_payload(),
    )

    assert response.status_code == 400


def test_day89_non_object_request_body_is_rejected():
    client = TestClient(create_app())

    response = client.post(
        "/counterfactual-capability",
        json=["not", "an", "object"],
    )

    assert response.status_code == 422
