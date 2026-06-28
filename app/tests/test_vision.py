"""
Tests for the vision module.
Ollama API calls are mocked — no running Ollama needed for unit tests.
Integration tests (marked requires_ollama) call the real model.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from nexus.core.vision import VisionEngine, VisionResult, _parse_marker_number


# ---------------------------------------------------------------------------
# Unit tests (no Ollama)
# ---------------------------------------------------------------------------

class TestParseMarkerNumber:
    def test_parses_plain_number(self):
        assert _parse_marker_number("42") == 42

    def test_parses_number_in_sentence(self):
        assert _parse_marker_number("The element is closest to marker 175.") == 175

    def test_returns_none_for_out_of_range(self):
        assert _parse_marker_number("9999") is None

    def test_returns_first_valid_number(self):
        assert _parse_marker_number("Maybe 5 or 10") == 5

    def test_returns_none_for_not_found(self):
        assert _parse_marker_number("NOT_FOUND") is None

    def test_returns_none_for_empty(self):
        assert _parse_marker_number("") is None


class TestVisionEngine:
    @pytest.fixture
    def engine_with_mocked_client(self):
        with patch("nexus.core.vision.ollama.Client") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client
            mock_client.list.return_value = MagicMock(models=[MagicMock(model="qwen3-vl:8b")])
            engine = VisionEngine()
            engine._client = mock_client
            yield engine, mock_client

    def test_find_element_returns_result_on_valid_response(self, engine_with_mocked_client):
        engine, mock_client = engine_with_mocked_client
        mock_client.chat.return_value = MagicMock(
            message=MagicMock(content="150")
        )
        img = Image.new("RGB", (1280, 800), (40, 40, 40))
        result = engine.find_element("Search button", screenshot=img)

        assert result is not None
        assert isinstance(result, VisionResult)
        assert 0 <= result.x <= 1280
        assert 0 <= result.y <= 800

    def test_find_element_returns_none_on_not_found(self, engine_with_mocked_client):
        engine, mock_client = engine_with_mocked_client
        mock_client.chat.return_value = MagicMock(
            message=MagicMock(content="NOT_FOUND")
        )
        img = Image.new("RGB", (1280, 800), (0, 0, 0))
        result = engine.find_element("Invisible button", screenshot=img)

        assert result is None

    def test_find_element_returns_none_on_exception(self, engine_with_mocked_client):
        engine, mock_client = engine_with_mocked_client
        mock_client.chat.side_effect = Exception("Connection refused")
        img = Image.new("RGB", (1280, 800), (20, 20, 20))
        result = engine.find_element("Any button", screenshot=img)

        assert result is None

    def test_describe_screen_returns_string(self, engine_with_mocked_client):
        engine, mock_client = engine_with_mocked_client
        mock_client.chat.return_value = MagicMock(
            message=MagicMock(content="Safari is open showing google.com with a search bar.")
        )
        img = Image.new("RGB", (1280, 800), (30, 30, 30))
        description = engine.describe_screen(screenshot=img)

        assert isinstance(description, str)
        assert len(description) > 0

    def test_describe_screen_fallback_on_error(self, engine_with_mocked_client):
        engine, mock_client = engine_with_mocked_client
        mock_client.chat.side_effect = ConnectionError("Ollama down")
        img = Image.new("RGB", (1280, 800))
        result = engine.describe_screen(screenshot=img)

        assert result == "Unable to describe screen."


class TestVisionResult:
    def test_vision_result_fields(self):
        result = VisionResult(x=640.0, y=400.0, confidence="medium", raw_response="150")
        assert result.x == 640.0
        assert result.y == 400.0
        assert result.confidence == "medium"
