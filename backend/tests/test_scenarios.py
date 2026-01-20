import pytest


def test_create_scenario(client):
    """Test creating a new scenario."""
    response = client.post(
        "/api/scenarios",
        json={
            "name": "Fantasy World",
            "genre": "Fantasy",
            "tone": "Epic",
            "setting": "A medieval kingdom",
            "premise": "Dragons have returned",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Fantasy World"
    assert data["genre"] == "Fantasy"
    assert "id" in data


def test_list_scenarios(client):
    """Test listing scenarios."""
    client.post("/api/scenarios", json={"name": "Scenario 1"})
    client.post("/api/scenarios", json={"name": "Scenario 2"})

    response = client.get("/api/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["scenarios"]) == 2


def test_get_scenario(client):
    """Test getting a single scenario."""
    create_response = client.post(
        "/api/scenarios",
        json={"name": "Test Scenario"},
    )
    scenario_id = create_response.json()["id"]

    response = client.get(f"/api/scenarios/{scenario_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Scenario"


def test_get_scenario_not_found(client):
    """Test getting a non-existent scenario."""
    response = client.get("/api/scenarios/999")
    assert response.status_code == 404


def test_update_scenario(client):
    """Test updating a scenario."""
    create_response = client.post(
        "/api/scenarios",
        json={"name": "Original Name"},
    )
    scenario_id = create_response.json()["id"]

    response = client.put(
        f"/api/scenarios/{scenario_id}",
        json={"name": "Updated Name", "genre": "Sci-Fi"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["genre"] == "Sci-Fi"


def test_delete_scenario(client):
    """Test deleting a scenario."""
    create_response = client.post(
        "/api/scenarios",
        json={"name": "To Delete"},
    )
    scenario_id = create_response.json()["id"]

    response = client.delete(f"/api/scenarios/{scenario_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/scenarios/{scenario_id}")
    assert get_response.status_code == 404
