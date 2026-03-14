from __future__ import annotations

import json
import time
from typing import NoReturn

import typer

from metainflow_studio_cli.core.errors import ExternalError, MetainflowError, ProcessingError, ValidationError
from metainflow_studio_cli.services.doc_parse.service import parse_document
from metainflow_studio_cli.services.web_search.service import search_summary


app = typer.Typer(help="Metainflow studio CLI")


@app.callback()
def root() -> None:
    """Metainflow command group entrypoint."""


@app.command("parse-doc")
def parse_doc(file: str = typer.Option(..., "--file"), output: str = typer.Option("text", "--output")) -> None:
    envelope: dict | None = None
    try:
        envelope = parse_document(file_or_url=file, output=output)
    except ValidationError as exc:
        _emit_error(output, 2, str(exc), retryable=False)
    except ProcessingError as exc:
        _emit_error(output, 1, str(exc), retryable=False)
    except ExternalError as exc:
        _emit_error(output, 3, str(exc), retryable=True)
    except MetainflowError as exc:
        _emit_error(output, 1, str(exc), retryable=False)

    if envelope is None:
        _emit_error(output, 1, "unknown error", retryable=False)

    if output == "json":
        typer.echo(json.dumps(envelope, ensure_ascii=False))
    else:
        typer.echo(envelope["data"]["markdown"])


@app.command("search-summary")
def search_summary_command(
    query: str = typer.Option(..., "--query"),
    instruction: str = typer.Option("", "--instruction"),
    output: str = typer.Option("text", "--output", "-o"),
) -> None:
    started = time.perf_counter()
    envelope: dict | None = None
    try:
        envelope = search_summary(query=query, instruction=instruction, output=output)
    except ValidationError as exc:
        if output == "json":
            _emit_search_error(query, instruction, 2, str(exc), retryable=False, latency_ms=_elapsed_ms(started))
        _emit_error(output, 2, str(exc), retryable=False)
    except ProcessingError as exc:
        if output == "json":
            _emit_search_error(query, instruction, 1, str(exc), retryable=False, latency_ms=_elapsed_ms(started))
        _emit_error(output, 1, str(exc), retryable=False)
    except ExternalError as exc:
        if output == "json":
            _emit_search_error(query, instruction, 3, str(exc), retryable=True, latency_ms=_elapsed_ms(started))
        _emit_error(output, 3, str(exc), retryable=True)
    except MetainflowError as exc:
        if output == "json":
            _emit_search_error(query, instruction, 1, str(exc), retryable=False, latency_ms=_elapsed_ms(started))
        _emit_error(output, 1, str(exc), retryable=False)

    if envelope is None:
        _emit_error(output, 1, "unknown error", retryable=False)

    if output == "json":
        typer.echo(json.dumps(envelope, ensure_ascii=False))
        if envelope.get("success") is False and envelope.get("error"):
            raise typer.Exit(code=int(envelope["error"]["code"]))
    else:
        typer.echo(envelope["data"]["summary"])


def _emit_search_error(query: str, instruction: str, code: int, message: str, retryable: bool, latency_ms: int) -> NoReturn:
    payload = {
        "success": False,
        "data": {
            "summary": "",
            "query": query.strip(),
            "instruction": instruction.strip(),
            "results": [],
        },
        "meta": {
            "search_provider": "",
            "summary_provider": "",
            "model": "",
            "latency_ms": latency_ms,
            "request_id": "",
        },
        "error": {"code": code, "message": message, "retryable": retryable},
    }
    typer.echo(json.dumps(payload, ensure_ascii=False))
    raise typer.Exit(code=code)


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _emit_error(output: str, code: int, message: str, retryable: bool) -> NoReturn:
    if output == "json":
        payload = {
            "success": False,
            "data": None,
            "meta": {"parser": "", "latency_ms": 0, "request_id": ""},
            "error": {"code": code, "message": message, "retryable": retryable},
        }
        typer.echo(json.dumps(payload, ensure_ascii=False))
    else:
        typer.echo(f"error: {message}", err=True)
    raise typer.Exit(code=code)


if __name__ == "__main__":
    app()
