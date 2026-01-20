# Testing Guide

This document provides detailed instructions for testing the Storyteller application.

## Test Overview

| Component | Framework | Tests | Coverage |
|-----------|-----------|-------|----------|
| Backend | pytest | 21 | Characters, Scenarios, Stories, Health |
| Frontend | vitest | 12 | App rendering, Zustand stores |

## Backend Testing

### Setup

```bash
cd backend

# Install test dependencies (included in requirements.txt)
pip install pytest pytest-asyncio pytest-cov
```

### Running Tests

```bash
# Run all tests with verbose output
python -m pytest tests/ -v

# Run with short traceback on failures
python -m pytest tests/ -v --tb=short

# Run specific test file
python -m pytest tests/test_characters.py -v

# Run specific test function
python -m pytest tests/test_characters.py::test_create_character -v

# Run tests matching a pattern
python -m pytest tests/ -v -k "create"
```

### Coverage Reports

```bash
# Run with coverage
python -m pytest tests/ --cov=app --cov-report=term-missing

# Generate HTML coverage report
python -m pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser

# Generate XML coverage report (for CI)
python -m pytest tests/ --cov=app --cov-report=xml
```

### Test Structure

```
backend/tests/
├── __init__.py
├── conftest.py          # Pytest fixtures (test DB, client)
├── test_characters.py   # Character CRUD tests
├── test_scenarios.py    # Scenario CRUD tests
├── test_stories.py      # Story CRUD tests
└── test_health.py       # Health endpoint tests
```

### Key Fixtures (conftest.py)

- `db`: Fresh SQLite in-memory database for each test
- `client`: FastAPI TestClient with test database

### Test Categories

#### Character Tests (6 tests)
- `test_create_character` - Create with all fields
- `test_list_characters` - List with pagination
- `test_get_character` - Get by ID
- `test_get_character_not_found` - 404 handling
- `test_update_character` - Partial update
- `test_delete_character` - Delete and verify

#### Scenario Tests (6 tests)
- `test_create_scenario` - Create with genre/tone
- `test_list_scenarios` - List all scenarios
- `test_get_scenario` - Get by ID
- `test_get_scenario_not_found` - 404 handling
- `test_update_scenario` - Update fields
- `test_delete_scenario` - Delete scenario

#### Story Tests (7 tests)
- `test_create_story` - Create basic story
- `test_create_story_with_characters` - Create with character assignments
- `test_list_stories` - List all stories
- `test_get_story` - Get by ID
- `test_get_story_not_found` - 404 handling
- `test_update_story` - Update title
- `test_delete_story` - Delete story and episodes

#### Health Tests (2 tests)
- `test_health_check` - Verify health endpoint
- `test_list_models` - List Ollama models

### Writing New Backend Tests

```python
# tests/test_example.py

def test_example_endpoint(client):
    """Test description."""
    # Arrange - set up test data
    client.post("/api/characters", json={"name": "Test"})

    # Act - perform the action
    response = client.get("/api/characters")

    # Assert - verify results
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
```

## Frontend Testing

### Setup

```bash
cd frontend

# Install dependencies (vitest included in package.json)
npm install
```

### Running Tests

```bash
# Run tests once
npm run test:run

# Run tests in watch mode (re-run on file changes)
npm run test

# Run with verbose output
npm run test:run -- --reporter=verbose

# Run specific test file
npm run test:run -- src/test/stores.test.ts

# Run tests matching a pattern
npm run test:run -- -t "storyStore"
```

### Coverage Reports

```bash
# Run with coverage
npm run test:run -- --coverage

# Coverage report will be in coverage/ directory
```

### Test Structure

```
frontend/src/test/
├── setup.ts           # Test setup (jest-dom)
├── App.test.tsx       # App component tests
└── stores.test.ts     # Zustand store tests
```

### Test Configuration (vite.config.ts)

```typescript
test: {
  globals: true,
  environment: 'jsdom',
  setupFiles: './src/test/setup.ts',
}
```

### Test Categories

#### App Tests (2 tests)
- `renders without crashing` - Basic render test
- `shows navigation links` - Navigation present

#### Story Store Tests (5 tests)
- `sets current story` - Story state management
- `sets episodes` - Episode list management
- `appends streaming content` - Token accumulation
- `adds streaming sentences` - Sentence queue
- `clears streaming` - Reset streaming state

#### Audio Store Tests (5 tests)
- `sets volume` - Volume control
- `sets playback rate` - Speed control
- `adds to queue` - TTS sentence queue
- `clears queue` - Reset audio state
- `advances to next sentence` - Queue progression

### Writing New Frontend Tests

```typescript
// src/test/example.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import MyComponent from '../components/MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent title="Test" />)
    expect(screen.getByText('Test')).toBeInTheDocument()
  })

  it('handles click events', async () => {
    const onClick = vi.fn()
    render(<MyComponent onClick={onClick} />)

    await userEvent.click(screen.getByRole('button'))
    expect(onClick).toHaveBeenCalled()
  })
})
```

### Testing Zustand Stores

```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import { useMyStore } from '../stores/myStore'

describe('myStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useMyStore.setState({ value: null })
  })

  it('updates state', () => {
    useMyStore.getState().setValue('test')
    expect(useMyStore.getState().value).toBe('test')
  })
})
```

## Integration Testing

### Manual Integration Tests

1. **Character/Scenario CRUD**
   - Create, edit, list, delete characters through UI
   - Create, edit, list, delete scenarios through UI

2. **Story Creation**
   - Select scenario and characters
   - Verify story appears in list

3. **Episode Generation** (requires Ollama)
   - Generate first episode
   - Verify streaming text display
   - Generate follow-up episodes
   - Verify story continuity

4. **TTS Integration** (requires Kokoro)
   - Generate episode
   - Play audio narration
   - Test volume/speed controls

5. **Story Forking**
   - Fork from specific episode
   - Verify new story created
   - Generate divergent episodes

### API Testing with curl

```bash
# Health check
curl http://localhost:8000/api/health

# Create character
curl -X POST http://localhost:8000/api/characters \
  -H "Content-Type: application/json" \
  -d '{"name": "Hero", "personality": "Brave"}'

# List characters
curl http://localhost:8000/api/characters

# Create scenario
curl -X POST http://localhost:8000/api/scenarios \
  -H "Content-Type: application/json" \
  -d '{"name": "Fantasy", "genre": "Fantasy", "tone": "Epic"}'

# Create story
curl -X POST http://localhost:8000/api/stories \
  -H "Content-Type: application/json" \
  -d '{"title": "My Adventure", "scenario_id": 1, "characters": []}'

# Generate episode (SSE stream)
curl -X POST http://localhost:8000/api/stories/1/episodes/generate \
  -H "Content-Type: application/json" \
  -d '{"guidance": "Start with action"}'
```

## CI/CD Testing

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          python -m pytest tests/ -v --cov=app

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: |
          cd frontend
          npm install
      - name: Run tests
        run: |
          cd frontend
          npm run test:run
```

## Troubleshooting Tests

### Backend Test Issues

```bash
# Module not found errors
pip install -e .  # Install package in editable mode

# Database errors
# Tests use in-memory SQLite, ensure conftest.py is present

# Async test issues
pip install pytest-asyncio
```

### Frontend Test Issues

```bash
# Clear cache
rm -rf node_modules/.vite
npm run test:run

# jsdom errors
npm install jsdom @testing-library/jest-dom

# React warnings
# Ensure test wrapper includes all providers (QueryClient, Router)
```

## Performance Testing

### Load Testing with locust

```python
# locustfile.py
from locust import HttpUser, task, between

class StorytellerUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_characters(self):
        self.client.get("/api/characters")

    @task(2)
    def list_stories(self):
        self.client.get("/api/stories")

    @task(1)
    def health_check(self):
        self.client.get("/api/health")
```

```bash
# Run load test
pip install locust
locust -f locustfile.py --host=http://localhost:8000
```

## Test Data

### Sample Test Data

```python
# Sample character
character = {
    "name": "Elena Stormbringer",
    "description": "A tall woman with silver hair",
    "personality": "Determined and compassionate",
    "motivations": "To protect her homeland",
    "backstory": "Once a soldier, now a wanderer"
}

# Sample scenario
scenario = {
    "name": "The Shattered Realm",
    "setting": "A world broken by ancient magic",
    "time_period": "Post-apocalyptic fantasy",
    "genre": "Fantasy",
    "tone": "Dark but hopeful",
    "premise": "Magic has returned, but at a cost"
}
```
