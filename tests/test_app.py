import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore original activities state before each test"""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original))


def test_root_redirects():
    # Arrange: no setup needed

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities():
    # Arrange

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert "Chess Club" in response.json()


def test_signup_success_and_duplicate():
    activity = "Chess Club"
    new_email = "test@school.edu"

    # Arrange – ensure not already signed up
    if new_email in activities[activity]["participants"]:
        activities[activity]["participants"].remove(new_email)

    # Act
    resp1 = client.post(f"/activities/{activity}/signup", params={"email": new_email})

    # Assert
    assert resp1.status_code == 200
    assert new_email in activities[activity]["participants"]

    # Act – duplicate
    resp2 = client.post(f"/activities/{activity}/signup", params={"email": new_email})

    # Assert
    assert resp2.status_code == 400


def test_signup_nonexistent_activity():
    # Arrange
    fake = "NotReal"

    # Act
    resp = client.post(f"/activities/{fake}/signup", params={"email": "a@b.com"})

    # Assert
    assert resp.status_code == 404


def test_remove_participant_success_and_failure():
    activity = "Chess Club"
    existing = activities[activity]["participants"][0]

    # Arrange – ensure participant present
    assert existing in activities[activity]["participants"]

    # Act – remove
    resp = client.delete(f"/activities/{activity}/participants", params={"email": existing})

    # Assert
    assert resp.status_code == 200
    assert existing not in activities[activity]["participants"]

    # Act – remove non-member
    resp2 = client.delete(f"/activities/{activity}/participants", params={"email": "noone@here.com"})
    # Assert
    assert resp2.status_code == 404

    # Act – non-existing activity
    resp3 = client.delete("/activities/Nope/participants", params={"email": existing})
    # Assert
    assert resp3.status_code == 404
