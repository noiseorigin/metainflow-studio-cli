import json

from typer.testing import CliRunner

from metainflow_studio_cli.core.errors import ExternalError
from metainflow_studio_cli.main import app


runner = CliRunner()


def test_search_summary_json_output(monkeypatch) -> None:
    def fake_search_summary(query: str, instruction: str, output: str) -> dict:
        assert query == "React 19 新特性"
        assert instruction == "按功能分类整理"
        assert output == "json"
        return {
            "success": True,
            "data": {
                "summary": "summary text",
                "query": query,
                "instruction": instruction,
                "results": [],
            },
            "meta": {
                "search_provider": "baidu-playwright",
                "summary_provider": "llm",
                "model": "search-model",
                "latency_ms": 10,
                "request_id": "resp_123",
            },
            "error": None,
        }

    monkeypatch.setattr("metainflow_studio_cli.main.search_summary", fake_search_summary)

    result = runner.invoke(
        app,
        ["search-summary", "--query", "React 19 新特性", "--instruction", "按功能分类整理", "--output", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["data"]["summary"] == "summary text"


def test_search_summary_text_output(monkeypatch) -> None:
    def fake_search_summary(query: str, instruction: str, output: str) -> dict:
        assert output == "text"
        return {
            "success": True,
            "data": {
                "summary": "summary text",
                "query": query,
                "instruction": instruction,
                "results": [],
            },
            "meta": {
                "search_provider": "baidu-playwright",
                "summary_provider": "llm",
                "model": "search-model",
                "latency_ms": 0,
                "request_id": "resp_123",
            },
            "error": None,
        }

    monkeypatch.setattr("metainflow_studio_cli.main.search_summary", fake_search_summary)

    result = runner.invoke(app, ["search-summary", "--query", "React 19 新特性"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "summary text"


def test_search_summary_empty_query_returns_validation_error() -> None:
    result = runner.invoke(app, ["search-summary", "--query", "   ", "--output", "json"])

    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["success"] is False
    assert payload["data"]["results"] == []
    assert payload["meta"]["search_provider"] == ""
    assert payload["error"]["message"] == "--query must not be empty"


def test_search_summary_help_works() -> None:
    result = runner.invoke(app, ["search-summary", "--help"])

    assert result.exit_code == 0
    assert "--query" in result.stdout
    assert "--instruction" in result.stdout


def test_search_summary_external_error_returns_retryable_payload(monkeypatch) -> None:
    def fake_search_summary(query: str, instruction: str, output: str) -> dict:
        raise ExternalError("web search request failed")

    monkeypatch.setattr("metainflow_studio_cli.main.search_summary", fake_search_summary)

    result = runner.invoke(app, ["search-summary", "--query", "React 19 新特性", "--output", "json"])

    assert result.exit_code == 3
    payload = json.loads(result.stdout)
    assert payload["success"] is False
    assert payload["error"]["retryable"] is True
    assert payload["error"]["message"] == "web search request failed"


def test_search_summary_json_preserves_results_when_summary_fails(monkeypatch) -> None:
    def fake_search_summary(query: str, instruction: str, output: str) -> dict:
        return {
            "success": False,
            "data": {
                "summary": "",
                "query": query,
                "instruction": instruction,
                "results": [{"title": "Result 1", "url": "https://example.com/1", "snippet": "snippet 1"}],
            },
            "meta": {
                "search_provider": "baidu-playwright",
                "summary_provider": "llm",
                "model": "search-model",
                "latency_ms": 0,
                "request_id": "",
            },
            "error": {
                "code": 3,
                "message": "web search summary request failed",
                "retryable": True,
            },
        }

    monkeypatch.setattr("metainflow_studio_cli.main.search_summary", fake_search_summary)

    result = runner.invoke(app, ["search-summary", "--query", "React 19 新特性", "--output", "json"])

    assert result.exit_code == 3
    payload = json.loads(result.stdout)
    assert payload["success"] is False
    assert payload["data"]["results"][0]["url"] == "https://example.com/1"


def test_search_summary_text_mode_uses_plain_error_output(monkeypatch) -> None:
    def fake_search_summary(query: str, instruction: str, output: str) -> dict:
        raise ExternalError("web search request failed")

    monkeypatch.setattr("metainflow_studio_cli.main.search_summary", fake_search_summary)

    result = runner.invoke(app, ["search-summary", "--query", "React 19 新特性"])

    assert result.exit_code == 3
    assert result.stdout == ""
    assert "error: web search request failed" in result.stderr


def test_search_summary_json_error_includes_latency(monkeypatch) -> None:
    def fake_search_summary(query: str, instruction: str, output: str) -> dict:
        raise ExternalError("web search request failed")

    monkeypatch.setattr("metainflow_studio_cli.main.search_summary", fake_search_summary)

    result = runner.invoke(app, ["search-summary", "--query", "React 19 新特性", "--output", "json"])

    payload = json.loads(result.stdout)
    assert result.exit_code == 3
    assert isinstance(payload["meta"]["latency_ms"], int)
    assert payload["meta"]["latency_ms"] >= 0
