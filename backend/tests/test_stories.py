import pytest


def test_create_story(client):
    """Test creating a new story."""
    # First create a scenario
    scenario_response = client.post(
        "/api/scenarios",
        json={"name": "Test Scenario"},
    )
    scenario_id = scenario_response.json()["id"]

    # Create a story
    response = client.post(
        "/api/stories",
        json={
            "title": "My Story",
            "scenario_id": scenario_id,
            "characters": [],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My Story"
    assert data["status"] == "draft"
    assert "id" in data


def test_create_story_with_characters(client):
    """Test creating a story with characters."""
    # Create scenario
    scenario_response = client.post(
        "/api/scenarios",
        json={"name": "Test Scenario"},
    )
    scenario_id = scenario_response.json()["id"]

    # Create character
    character_response = client.post(
        "/api/characters",
        json={"name": "Hero"},
    )
    character_id = character_response.json()["id"]

    # Create story with character
    response = client.post(
        "/api/stories",
        json={
            "title": "My Story",
            "scenario_id": scenario_id,
            "characters": [
                {"character_id": character_id, "role": "protagonist"}
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data["characters"]) == 1
    assert data["characters"][0]["role"] == "protagonist"


def test_list_stories(client):
    """Test listing stories."""
    # Create scenario
    scenario_response = client.post(
        "/api/scenarios",
        json={"name": "Test Scenario"},
    )
    scenario_id = scenario_response.json()["id"]

    # Create stories
    client.post(
        "/api/stories",
        json={"title": "Story 1", "scenario_id": scenario_id, "characters": []},
    )
    client.post(
        "/api/stories",
        json={"title": "Story 2", "scenario_id": scenario_id, "characters": []},
    )

    response = client.get("/api/stories")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


def test_get_story(client):
    """Test getting a single story."""
    # Create scenario and story
    scenario_response = client.post(
        "/api/scenarios",
        json={"name": "Test Scenario"},
    )
    scenario_id = scenario_response.json()["id"]

    create_response = client.post(
        "/api/stories",
        json={"title": "Test Story", "scenario_id": scenario_id, "characters": []},
    )
    story_id = create_response.json()["id"]

    response = client.get(f"/api/stories/{story_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Test Story"


def test_get_story_not_found(client):
    """Test getting a non-existent story."""
    response = client.get("/api/stories/999")
    assert response.status_code == 404


def test_update_story(client):
    """Test updating a story."""
    # Create scenario and story
    scenario_response = client.post(
        "/api/scenarios",
        json={"name": "Test Scenario"},
    )
    scenario_id = scenario_response.json()["id"]

    create_response = client.post(
        "/api/stories",
        json={"title": "Original", "scenario_id": scenario_id, "characters": []},
    )
    story_id = create_response.json()["id"]

    response = client.put(
        f"/api/stories/{story_id}",
        json={"title": "Updated"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"


def test_delete_story(client):
    """Test deleting a story."""
    # Create scenario and story
    scenario_response = client.post(
        "/api/scenarios",
        json={"name": "Test Scenario"},
    )
    scenario_id = scenario_response.json()["id"]

    create_response = client.post(
        "/api/stories",
        json={"title": "To Delete", "scenario_id": scenario_id, "characters": []},
    )
    story_id = create_response.json()["id"]

    response = client.delete(f"/api/stories/{story_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/stories/{story_id}")
    assert get_response.status_code == 404
