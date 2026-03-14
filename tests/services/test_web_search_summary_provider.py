import pytest
import httpx

from metainflow_studio_cli.core.config import Settings
from metainflow_studio_cli.core.errors import ExternalError, ProcessingError
from metainflow_studio_cli.services.web_search.summary_provider import summarize_search_results


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_summarize_search_results_builds_plain_model_request(monkeypatch) -> None:
    seen: dict = {}

    def fake_post(url: str, *, headers: dict, json: dict, timeout: int) -> _FakeResponse:
        seen["url"] = url
        seen["json"] = json
        return _FakeResponse(
            {
                "id": "chatcmpl_123",
                "choices": [{"message": {"content": "summary text"}}],
                "model": "search-model",
            }
        )

    monkeypatch.setattr("metainflow_studio_cli.services.web_search.summary_provider.httpx.post", fake_post)

    settings = Settings(
        provider_base_url="https://api.example.com/v1",
        provider_api_key="secret",
        provider_timeout_seconds=30,
        provider_max_retries=2,
        provider_model_doc_parse="doc-model",
        provider_model_web_search="search-model",
        web_search_page_timeout_seconds=30,
    )

    result = summarize_search_results(
        query="React 19 新特性",
        instruction="按功能分类整理",
        results=[{"title": "R1", "url": "https://example.com/1", "snippet": "S1"}],
        settings=settings,
    )

    assert seen["url"] == "https://api.example.com/v1/chat/completions"
    assert seen["json"]["model"] == "search-model"
    assert "tools" not in seen["json"]
    assert seen["json"]["messages"][1]["content"].count("https://example.com/1") == 1
    assert result["summary"] == "summary text"
    assert result["model"] == "search-model"
    assert result["request_id"] == "chatcmpl_123"


def test_summarize_search_results_raises_processing_error_for_bad_response(monkeypatch) -> None:
    def fake_post(url: str, *, headers: dict, json: dict, timeout: int) -> _FakeResponse:
        return _FakeResponse({"id": "chatcmpl_123", "choices": []})

    monkeypatch.setattr("metainflow_studio_cli.services.web_search.summary_provider.httpx.post", fake_post)

    settings = Settings(
        provider_base_url="https://api.example.com/v1",
        provider_api_key="secret",
        provider_timeout_seconds=30,
        provider_max_retries=2,
        provider_model_doc_parse="doc-model",
        provider_model_web_search="search-model",
        web_search_page_timeout_seconds=30,
    )

    with pytest.raises(ProcessingError, match="summary response missing message content"):
        summarize_search_results(query="query", instruction="", results=[], settings=settings)


def test_summarize_search_results_maps_http_errors(monkeypatch) -> None:
    def fake_post(url: str, *, headers: dict, json: dict, timeout: int):
        raise httpx.HTTPError("boom")

    monkeypatch.setattr("metainflow_studio_cli.services.web_search.summary_provider.httpx.post", fake_post)

    settings = Settings(
        provider_base_url="https://api.example.com/v1",
        provider_api_key="secret",
        provider_timeout_seconds=30,
        provider_max_retries=2,
        provider_model_doc_parse="doc-model",
        provider_model_web_search="search-model",
        web_search_page_timeout_seconds=30,
    )

    with pytest.raises(ExternalError, match="web search summary request failed"):
        summarize_search_results(query="query", instruction="", results=[], settings=settings)
