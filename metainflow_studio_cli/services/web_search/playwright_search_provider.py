from __future__ import annotations

from urllib.parse import urlencode

from metainflow_studio_cli.core.errors import ExternalError

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - exercised by runtime setup, not unit tests
    sync_playwright = None


def search_web_with_playwright(query: str, timeout_seconds: int = 30) -> dict:
    if sync_playwright is None:
        raise ExternalError("Playwright is not installed")

    url = f"https://www.baidu.com/s?{urlencode({'wd': query})}"
    timeout_ms = timeout_seconds * 1000
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)

            if page.locator("#captcha, .vcode-body").count() > 0:
                browser.close()
                raise ExternalError("baidu search requires captcha verification")

            if page.locator(".no-result").count() > 0:
                browser.close()
                return {"provider": "baidu-playwright", "results": []}

            if page.locator("#content_left .result, #content_left .c-container").count() == 0:
                browser.close()
                raise ExternalError("search page format changed or request was blocked")

            results = []
            for node in page.query_selector_all("#content_left .result, #content_left .c-container"):
                title_handle = _select_child(node, "h3 a")
                if title_handle is None:
                    continue
                title = _read_text(title_handle)
                url = _read_href(title_handle)
                snippet_handle = _select_first_child(
                    node,
                    [
                        '[data-sanssr-cmpt="card/www-summary"]',
                        ".c-abstract, .content-right_8Zs40",
                    ],
                )
                snippet = _read_text(snippet_handle) if snippet_handle is not None else ""
                if title and url:
                    results.append({"title": title, "url": url, "snippet": snippet})

            browser.close()
    except ExternalError:
        raise
    except Exception as exc:
        raise ExternalError("failed to launch Playwright search") from exc

    return {"provider": "baidu-playwright", "results": results}


def _select_child(node, selector: str):
    if hasattr(node, "locator"):
        child = node.locator(selector)
        if hasattr(child, "count") and child.count() > 0:
            return child
        return None
    if hasattr(node, "query_selector"):
        return node.query_selector(selector)
    return None


def _read_text(node) -> str:
    if node is None:
        return ""
    text = node.inner_text() if hasattr(node, "inner_text") else ""
    return text.strip()


def _read_href(node) -> str:
    if node is None or not hasattr(node, "get_attribute"):
        return ""
    return (node.get_attribute("href") or "").strip()


def _select_first_child(node, selectors: list[str]):
    for selector in selectors:
        child = _select_child(node, selector)
        if child is not None:
            return child
    return None
