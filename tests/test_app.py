import uuid
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


def random_email():
    # Avoid '+' in the email local part to prevent '+' being interpreted as space in URL-encoded query strings
    return f"test{uuid.uuid4().hex[:8]}@example.com"


def test_get_activities_has_cache_control_header():
    resp = client.get("/activities")
    assert resp.status_code == 200
    assert resp.headers.get("Cache-Control") == "no-store, max-age=0"
    data = resp.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data


def test_signup_and_reflects_in_get():
    email = random_email()
    activity = "Art Club"

    # ensure not present
    resp0 = client.get("/activities")
    assert resp0.status_code == 200
    assert email not in resp0.json()[activity]["participants"]

    # sign up
    resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 200
    assert "Signed up" in resp.json().get("message", "")

    # check reflected in GET
    resp2 = client.get("/activities")
    assert resp2.status_code == 200
    assert email in resp2.json()[activity]["participants"]

    # cleanup
    resp_del = client.delete(f"/activities/{activity}/signup?email={email}")
    assert resp_del.status_code == 200


def test_duplicate_signup_fails():
    email = random_email()
    activity = "Drama Club"

    try:
        resp = client.post(f"/activities/{activity}/signup?email={email}")
        assert resp.status_code == 200

        # duplicate should fail
        resp2 = client.post(f"/activities/{activity}/signup?email={email}")
        assert resp2.status_code == 400
        assert "already signed up" in resp2.json().get("detail", "").lower()
    finally:
        # cleanup if present
        client.delete(f"/activities/{activity}/signup?email={email}")


def test_unregister_nonexistent_fails():
    email = random_email()
    activity = "Debate Team"

    resp = client.delete(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 400
    assert "not signed up" in resp.json().get("detail", "").lower()
