import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_notification_service, get_ticket_service
from app.main import app
from tests.fakes import InMemoryContext


@pytest.fixture
def client():
    context = InMemoryContext()
    app.dependency_overrides[get_ticket_service] = lambda: context.service
    app.dependency_overrides[get_notification_service] = lambda: context.notifications
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_ticket(client: TestClient) -> dict:
    response = client.post(
        "/api/tickets",
        json={"title": "UPS alarm", "asset_code": "sede-are", "reported_by": "Security guard"},
    )
    assert response.status_code == 201
    return response.json()


def test_create_ticket_returns_pending_ticket_with_allowed_transitions(client):
    ticket = create_ticket(client)

    assert ticket["status"] == "PENDING"
    assert ticket["asset_code"] == "SEDE-ARE"
    assert {transition["to_status"] for transition in ticket["allowed_transitions"]} == {"IN_PROGRESS", "RESOLVED"}


def test_invalid_payload_returns_controlled_validation_error(client):
    response = client.post("/api/tickets", json={"title": "", "asset_code": "ATM 01"})

    body = response.json()
    assert response.status_code == 422
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert {detail["field"] for detail in body["error"]["details"]} >= {"title", "asset_code", "reported_by"}


def test_pending_to_resolved_without_diagnosis_returns_422(client):
    ticket = create_ticket(client)

    response = client.post(
        f"/api/tickets/{ticket['id']}/transitions",
        json={"to_status": "RESOLVED", "actor": "Operator"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


def test_not_allowed_transition_returns_409(client):
    ticket = create_ticket(client)

    response = client.post(
        f"/api/tickets/{ticket['id']}/transitions",
        json={"to_status": "CLOSED", "actor": "Operator"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_TRANSITION"


def test_transition_and_history_flow(client):
    ticket = create_ticket(client)

    moved = client.post(
        f"/api/tickets/{ticket['id']}/transitions",
        json={"to_status": "IN_PROGRESS", "actor": "Operator", "comment": "Technician assigned"},
    )
    detail = client.get(f"/api/tickets/{ticket['id']}").json()

    assert moved.status_code == 200
    assert detail["status"] == "IN_PROGRESS"
    assert [entry["event_type"] for entry in detail["history"]] == ["CREATED", "STATUS_CHANGED"]


def test_unknown_ticket_returns_404(client):
    response = client.get("/api/tickets/123456")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_filters_by_status(client):
    first = create_ticket(client)
    create_ticket(client)
    client.post(f"/api/tickets/{first['id']}/transitions", json={"to_status": "IN_PROGRESS", "actor": "Operator"})

    response = client.get("/api/tickets", params={"status": "IN_PROGRESS"})

    assert [ticket["id"] for ticket in response.json()] == [first["id"]]


def test_invalid_date_range_is_rejected(client):
    response = client.get("/api/tickets", params={"created_from": "2026-11-20", "created_to": "2026-11-01"})

    assert response.status_code == 422


def test_workflow_endpoint_exposes_state_machine(client):
    body = client.get("/api/workflow").json()

    assert body["statuses"] == ["PENDING", "IN_PROGRESS", "RESOLVED", "CLOSED"]
    assert len(body["transitions"]) == 6
