import src.app as app_module
from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def api(monkeypatch):
    test_activities = {
        "Chess Club": {
            "description": "Play chess",
            "schedule": "Fridays",
            "max_participants": 3,
            "participants": ["existing@example.com"],
        },
        "Art Club": {
            "description": "Make art",
            "schedule": "Wednesdays",
            "max_participants": 4,
            "participants": [],
        },
    }
    monkeypatch.setattr(app_module, "activities", test_activities)

    with TestClient(app_module.app) as client:
        yield client, test_activities


def test_root_redirects_to_static_index(api):
    # Arrange
    client, _ = api

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_data_without_cache(api):
    # Arrange
    client, test_activities = api

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == test_activities
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant(api):
    # Arrange
    client, test_activities = api
    activity_name = "Chess Club"
    email = "new@example.com"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert test_activities[activity_name]["participants"] == [
        "existing@example.com",
        email,
    ]


def test_signup_rejects_duplicate_participant(api):
    # Arrange
    client, test_activities = api
    activity_name = "Chess Club"
    email = "existing@example.com"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert test_activities[activity_name]["participants"] == [email]


def test_signup_rejects_unknown_activity(api):
    # Arrange
    client, test_activities = api

    # Act
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@example.com"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
    assert "Unknown Club" not in test_activities


def test_delete_signup_removes_participant(api):
    # Arrange
    client, test_activities = api
    activity_name = "Chess Club"
    email = "existing@example.com"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert test_activities[activity_name]["participants"] == []


def test_delete_signup_rejects_missing_participant(api):
    # Arrange
    client, test_activities = api
    activity_name = "Chess Club"
    email = "missing@example.com"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert test_activities[activity_name]["participants"] == [
        "existing@example.com"
    ]


def test_delete_signup_rejects_unknown_activity(api):
    # Arrange
    client, test_activities = api

    # Act
    response = client.delete(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@example.com"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
    assert "Unknown Club" not in test_activities