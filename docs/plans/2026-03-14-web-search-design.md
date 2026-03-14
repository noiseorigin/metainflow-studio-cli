# Web Search Design

## Goal

Add a second search-oriented agent skill to `metainflow-studio-cli`: `metainflow-web-search`.

This skill should keep the same usage style as `miaoda-web-search`: when the user has no specific URL and wants internet information by keyword, the agent should use a single search-and-summary command with optional AI instruction control and either text or JSON output.

The search step must be implemented by `metainflow-studio-cli` itself rather than depending on provider-native web-search tools, so that model switching does not break search behavior.

## Recommended Approach

Keep the external skill usage aligned with `miaoda-web-search`, but split the internal pipeline into two independent layers:

- a local search acquisition layer owned by `metainflow-studio-cli`
- a model-based summary layer that only consumes normalized search results

This preserves the requested user experience while ensuring search capability does not depend on provider-specific web-search features.

## Alternatives Considered

### Provider-native web search

This was the first attempt, but it makes `search-summary` dependent on provider-specific endpoints and tool support. Real verification showed that a provider can support ordinary model calls while not supporting the expected web-search interface. That violates the requirement that switching models should still work.

### Full self-managed crawler and search index

This would maximize control, but it is too large for the second skill. It introduces crawling policy, indexing, freshness management, and ranking complexity that is not needed to establish the first usable search experience.

## CLI Design

Keep the same command:

```bash
metainflow search-summary --query <keywords> --instruction <text> --output text|json
```

### Arguments

- `--query`: required, search keywords
- `--instruction`: optional, extra summary instruction for filtering, comparison, translation, or formatting
- `--output`, `-o`: optional, `text` or `json`, default `text`

## Command Boundary

The user-facing boundary stays the same as the reference skill:

- no concrete URL -> `metainflow search-summary`
- concrete URL -> future `metainflow web-crawl`
- search first, then read a page -> `search-summary` first, future `web-crawl` second

## Architecture

New module layout:

```text
metainflow_studio_cli/services/web_search/
  search_provider.py
  summary_provider.py
  service.py
```

### Responsibilities

- `main.py`
  - parse CLI arguments
  - map errors to exit codes
  - print text or JSON output
- `search_provider.py`
  - perform keyword search using a metainflow-owned acquisition strategy
  - normalize raw result entries into `title / url / snippet`
- `summary_provider.py`
  - send normalized search results plus optional instruction to the configured LLM
  - return final summary text and model metadata
- `service.py`
  - validate query and output mode
  - orchestrate search first, summary second
  - return the final response envelope

## Search Acquisition Strategy

The first version should not depend on model-native web-search tools.

Instead, it should:

1. build a query URL for the chosen search acquisition backend
2. fetch the search result page or structured endpoint
3. extract result items locally
4. normalize each item into:
   - `title`
   - `url`
   - `snippet`

The first implementation should keep this behind a dedicated search-provider abstraction so the backend can be changed later without changing the CLI or skill contract.

## Summary Strategy

Summary generation can still use the configured model, but only as a summarizer over already-fetched search results.

This means:

- switching models changes only summary quality or style
- switching models does not remove the ability to search
- `search-summary` remains functional even if provider-native web-search tools are unavailable

If a model call fails, the system should still preserve the normalized search results in the JSON response when possible.

## Output Contract

Keep the existing envelope:

- `success`
- `data`
- `meta`
- `error`

### Text Output

Print the final summary text.

### JSON Output

`data` should include:

- `summary`
- `query`
- `instruction`
- `results`

`meta` should include:

- `search_provider`
- `summary_provider`
- `model`
- `latency_ms`
- `request_id`

## Error Handling

Separate search-stage and summary-stage failures clearly.

- empty or invalid query -> `ValidationError`
- search acquisition failure -> `ExternalError`
- malformed search page or malformed model response -> `ProcessingError`
- summary call failure -> `ExternalError`

For JSON mode, if search succeeds but summary fails, the design should prefer returning a failure envelope that still contains normalized search results if the implementation can do so cleanly.

## Testing Strategy

Tests should cover:

- CLI help and argument parsing
- empty query rejection
- search result normalization
- summary payload construction from normalized results
- text and JSON output
- search failure mapping
- summary failure mapping
- partial-success behavior when search works but summary fails
- skill file parity with `miaoda-web-search` usage style

Use mocked HTTP responses first for both search acquisition and summary requests.

## Non-Goals For This Iteration

- browser automation
- clicking through result pages for full article extraction
- self-hosted crawler infrastructure
- persistent ranking models
- search history or caching system

## Acceptance Criteria

- `metainflow search-summary --help` works
- text and JSON outputs both work
- search results are acquired without provider-native web-search tools
- summary uses normalized result entries instead of provider search tools
- switching summary models does not change the search acquisition path
- `metainflow-web-search` exists and reads like `miaoda-web-search` with metainflow-specific command references
