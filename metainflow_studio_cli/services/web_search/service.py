from __future__ import annotations

import time

from metainflow_studio_cli.core.config import Settings
from metainflow_studio_cli.core.errors import ExternalError, ProcessingError, ValidationError
from metainflow_studio_cli.services.web_search.search_provider import search_web
from metainflow_studio_cli.services.web_search.summary_provider import summarize_search_results


def search_summary(query: str, instruction: str = "", output: str = "text") -> dict:
    if output not in {"text", "json"}:
        raise ValidationError("--output must be one of: text, json")

    started = time.perf_counter()
    normalized_query = query.strip()
    if not normalized_query:
        raise ValidationError("--query must not be empty")

    normalized_instruction = instruction.strip()
    settings = Settings.from_env()
    search_result = search_web(query=normalized_query, settings=settings)
    if search_result["results"]:
        try:
            summary_result = summarize_search_results(
                query=normalized_query,
                instruction=normalized_instruction,
                results=search_result["results"],
                settings=settings,
            )
        except ExternalError as exc:
            if output != "json":
                raise
            return {
                "success": False,
                "data": {
                    "summary": "",
                    "query": normalized_query,
                    "instruction": normalized_instruction,
                    "results": search_result["results"],
                },
                "meta": {
                    "search_provider": search_result["provider"],
                    "summary_provider": "llm",
                    "model": settings.summary_model,
                    "latency_ms": int((time.perf_counter() - started) * 1000),
                    "request_id": "",
                },
                "error": {"code": 3, "message": str(exc), "retryable": True},
            }
        except ProcessingError as exc:
            if output != "json":
                raise
            return {
                "success": False,
                "data": {
                    "summary": "",
                    "query": normalized_query,
                    "instruction": normalized_instruction,
                    "results": search_result["results"],
                },
                "meta": {
                    "search_provider": search_result["provider"],
                    "summary_provider": "llm",
                    "model": settings.summary_model,
                    "latency_ms": int((time.perf_counter() - started) * 1000),
                    "request_id": "",
                },
                "error": {"code": 1, "message": str(exc), "retryable": False},
            }
    else:
        summary_result = {
            "summary": "No relevant search results found.",
            "provider": "none",
            "model": "",
            "request_id": "",
        }

    return {
        "success": True,
        "data": {
            "summary": summary_result["summary"],
            "query": normalized_query,
            "instruction": normalized_instruction,
            "results": search_result["results"],
        },
        "meta": {
            "search_provider": search_result["provider"],
            "summary_provider": summary_result["provider"],
            "model": summary_result["model"],
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "request_id": summary_result["request_id"],
        },
        "error": None,
    }
