import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


@patch("shuttlekit.main.invoke_shuttle_agent", new_callable=AsyncMock)
def test_post_chat_returns_reply_and_session_id(mock_invoke, client):
    mock_invoke.return_value = {"session_id": "thread-abc", "reply": "Next shuttle at 3pm."}
    response = client.post(
        "/api/chat",
        json={"session_id": "thread-abc", "message": "When is the next bus?"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "session_id": "thread-abc",
        "reply": "Next shuttle at 3pm.",
    }
    mock_invoke.assert_called_once_with("thread-abc", "When is the next bus?")


@patch("shuttlekit.main.invoke_shuttle_agent", new_callable=AsyncMock)
def test_post_chat_passes_through_session_id(mock_invoke, client):
    mock_invoke.return_value = {"session_id": "s", "reply": "ok"}
    client.post("/api/chat", json={"session_id": "s", "message": "x"})
    mock_invoke.assert_called_once_with("s", "x")


def test_post_chat_validation_empty_message(client):
    response = client.post(
        "/api/chat",
        json={"session_id": "s", "message": ""},
    )
    assert response.status_code == 422


def test_post_chat_validation_empty_session_id(client):
    response = client.post(
        "/api/chat",
        json={"session_id": "", "message": "hi"},
    )
    assert response.status_code == 422


@patch("shuttlekit.main.invoke_shuttle_agent", new_callable=AsyncMock)
def test_post_chat_whitespace_only_message_returns_400(mock_invoke, client):
    mock_invoke.side_effect = ValueError("message must not be empty")
    response = client.post(
        "/api/chat",
        json={"session_id": "s", "message": "   "},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "message must not be empty"


@patch("shuttlekit.main.invoke_shuttle_agent", new_callable=AsyncMock)
def test_post_chat_os_error_returns_503(mock_invoke, client):
    mock_invoke.side_effect = OSError("connection refused")
    response = client.post(
        "/api/chat",
        json={"session_id": "s", "message": "hi"},
    )
    assert response.status_code == 503
    assert "MCP" in response.json()["detail"]


@patch("shuttlekit.main.invoke_shuttle_agent", new_callable=AsyncMock)
def test_post_chat_unexpected_error_returns_502(mock_invoke, client):
    mock_invoke.side_effect = RuntimeError("model exploded")
    response = client.post(
        "/api/chat",
        json={"session_id": "s", "message": "hi"},
    )
    assert response.status_code == 502
    assert "model exploded" in response.json()["detail"]
