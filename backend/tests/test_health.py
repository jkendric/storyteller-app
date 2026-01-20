import pytest


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data
    assert "ollama" in data["services"]
    assert "tts" in data["services"]


def test_list_models(client):
    """Test the models endpoint."""
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
