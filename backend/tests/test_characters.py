import pytest


def test_create_character(client):
    """Test creating a new character."""
    response = client.post(
        "/api/characters",
        json={
            "name": "John Doe",
            "description": "A mysterious stranger",
            "personality": "Quiet and observant",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["description"] == "A mysterious stranger"
    assert "id" in data


def test_list_characters(client):
    """Test listing characters."""
    # Create a character first
    client.post("/api/characters", json={"name": "Character 1"})
    client.post("/api/characters", json={"name": "Character 2"})

    response = client.get("/api/characters")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["characters"]) == 2


def test_get_character(client):
    """Test getting a single character."""
    # Create a character
    create_response = client.post(
        "/api/characters",
        json={"name": "Test Character"},
    )
    character_id = create_response.json()["id"]

    # Get the character
    response = client.get(f"/api/characters/{character_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Character"


def test_get_character_not_found(client):
    """Test getting a non-existent character."""
    response = client.get("/api/characters/999")
    assert response.status_code == 404


def test_update_character(client):
    """Test updating a character."""
    # Create a character
    create_response = client.post(
        "/api/characters",
        json={"name": "Original Name"},
    )
    character_id = create_response.json()["id"]

    # Update the character
    response = client.put(
        f"/api/characters/{character_id}",
        json={"name": "Updated Name"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


def test_delete_character(client):
    """Test deleting a character."""
    # Create a character
    create_response = client.post(
        "/api/characters",
        json={"name": "To Delete"},
    )
    character_id = create_response.json()["id"]

    # Delete the character
    response = client.delete(f"/api/characters/{character_id}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/api/characters/{character_id}")
    assert get_response.status_code == 404
