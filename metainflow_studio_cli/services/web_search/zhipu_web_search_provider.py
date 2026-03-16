from __future__ import annotations

import httpx

from metainflow_studio_cli.core.config import Settings
from metainflow_studio_cli.core.errors import ExternalError, ProcessingError


def search_web_with_provider(query: str, settings: Settings) -> dict:
    payload = {
        "tool": "web-search-pro",
        "messages": [{"role": "user", "content": query}],
        "search_engine": settings.search_provider_engine,
        "count": settings.search_result_count,
    }
    try:
        response = httpx.post(
            f"{settings.provider_base_url.rstrip('/')}/tools",
            headers={
                "Authorization": f"Bearer {settings.provider_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=settings.provider_timeout_seconds,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ExternalError("provider web search request failed") from exc

    body = response.json()
    search_result = body.get("search_result")
    if search_result is None:
        search_result = _extract_search_result_from_tool_calls(body)
    if not isinstance(search_result, list):
        raise ProcessingError("provider web search returned invalid search_result")

    normalized = []
    for item in search_result:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        url = str(item.get("link") or "").strip()
        snippet = str(item.get("content") or "").strip()
        if title and url:
            normalized.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "source": str(item.get("media") or "").strip(),
                    "publish_date": str(item.get("publish_date") or "").strip(),
                }
            )

    return {
        "provider": "zhipu-web-search",
        "request_id": str(body.get("request_id") or body.get("id") or ""),
        "results": normalized,
    }


def _extract_search_result_from_tool_calls(body: dict) -> list:
    choices = body.get("choices")
    if not isinstance(choices, list):
        return []
    for choice in choices:
        if not isinstance(choice, dict):
            continue
        message = choice.get("message")
        if not isinstance(message, dict):
            continue
        tool_calls = message.get("tool_calls")
        if not isinstance(tool_calls, list):
            continue
        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue
            search_result = tool_call.get("search_result")
            if isinstance(search_result, list):
                return search_result
    return []
