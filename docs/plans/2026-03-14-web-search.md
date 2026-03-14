# Web Search Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a new `metainflow search-summary` command plus a matching `metainflow-web-search` skill, with search acquisition implemented by `metainflow-studio-cli` itself and summary generation handled separately by the configured model.

**Architecture:** Reuse the current CLI -> service pattern, but split web search into two explicit stages: a metainflow-owned search acquisition layer and a model-backed summary layer. Keep the outward command and skill style aligned with `miaoda-web-search` while making search independent from provider-native web-search tools.

**Tech Stack:** Python 3.11, Typer, httpx, pytest

---

### Task 1: Add config coverage for web search summary model selection

**Files:**
- Modify: `metainflow_studio_cli/core/config.py`
- Test: `tests/test_config.py`

**Step 1: Write the failing test**

Add a test in `tests/test_config.py` that sets `PROVIDER_MODEL_WEB_SEARCH` and asserts config loading exposes that field.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -q`
Expected: FAIL because the config field is missing.

**Step 3: Write minimal implementation**

Add `PROVIDER_MODEL_WEB_SEARCH` support in `metainflow_studio_cli/core/config.py` while preserving current behavior.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_config.py metainflow_studio_cli/core/config.py
git commit -m "feat: add web search config"
```

### Task 2: Add metainflow-owned search result acquisition

**Files:**
- Create: `metainflow_studio_cli/services/web_search/search_provider.py`
- Create: `tests/services/test_web_search_search_provider.py`

**Step 1: Write the failing test**

Add tests that mock search-page fetching and assert:
- query URL is built correctly
- result entries are extracted locally
- output is normalized into `title`, `url`, and `snippet`
- malformed result pages raise `ProcessingError`

**Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_web_search_search_provider.py -q`
Expected: FAIL because the module does not exist.

**Step 3: Write minimal implementation**

Implement a search provider that:
- fetches search results without using provider-native web-search tools
- extracts result items from the returned payload or page content
- returns normalized entries only

**Step 4: Run test to verify it passes**

Run: `pytest tests/services/test_web_search_search_provider.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/services/test_web_search_search_provider.py metainflow_studio_cli/services/web_search/search_provider.py
git commit -m "feat: add web search result acquisition"
```

### Task 3: Add summary provider over normalized search results

**Files:**
- Create: `metainflow_studio_cli/services/web_search/summary_provider.py`
- Create: `tests/services/test_web_search_summary_provider.py`

**Step 1: Write the failing test**

Add tests that mock model interaction and assert:
- request payload is built from normalized search results, not provider-native web-search tools
- model comes from config
- provider response is normalized into summary text, model, and request id fields
- malformed model responses raise `ProcessingError`

**Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_web_search_summary_provider.py -q`
Expected: FAIL because the module does not exist.

**Step 3: Write minimal implementation**

Implement a summary provider that:
- accepts query, optional instruction, and normalized results
- builds a normal text-generation request
- returns summary text and metadata

**Step 4: Run test to verify it passes**

Run: `pytest tests/services/test_web_search_summary_provider.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/services/test_web_search_summary_provider.py metainflow_studio_cli/services/web_search/summary_provider.py
git commit -m "feat: add web search summary provider"
```

### Task 4: Add service orchestration and partial-failure behavior

**Files:**
- Create: `metainflow_studio_cli/services/web_search/service.py`
- Create: `tests/services/test_web_search_service.py`

**Step 1: Write the failing test**

Add tests that assert:
- service rejects empty query values
- service returns the standard envelope
- `data.summary`, `data.query`, `data.instruction`, and `data.results` are present on success
- summary-stage failure preserves search results in JSON mode if that contract is chosen
- search-stage failure maps to the correct error class

**Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_web_search_service.py -q`
Expected: FAIL because the service module does not exist or does not meet the new contract.

**Step 3: Write minimal implementation**

Implement service orchestration that:
- validates the query
- calls local search acquisition first
- calls summary provider second
- returns the normalized envelope
- preserves search results when summary fails, if JSON-mode partial-success behavior is implemented

**Step 4: Run test to verify it passes**

Run: `pytest tests/services/test_web_search_service.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/services/test_web_search_service.py metainflow_studio_cli/services/web_search/service.py
git commit -m "feat: add web search service orchestration"
```

### Task 5: Wire the CLI command to the revised service

**Files:**
- Modify: `metainflow_studio_cli/main.py`
- Create: `tests/cli/test_search_summary_json.py`
- Modify: `tests/test_cli_help.py`

**Step 1: Write the failing test**

Add CLI tests for:
- `metainflow search-summary --help`
- JSON output success path
- text output success path
- validation errors
- external search or summary failure mapping

**Step 2: Run test to verify it fails**

Run: `pytest tests/cli/test_search_summary_json.py tests/test_cli_help.py -q`
Expected: FAIL because the command is missing or follows the old provider-native contract.

**Step 3: Write minimal implementation**

Add or update `search-summary` in `metainflow_studio_cli/main.py` with parameters:
- `--query`
- `--instruction`
- `--output`, `-o`

Reuse the existing CLI error strategy and print either summary text or JSON.

**Step 4: Run test to verify it passes**

Run: `pytest tests/cli/test_search_summary_json.py tests/test_cli_help.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/cli/test_search_summary_json.py tests/test_cli_help.py metainflow_studio_cli/main.py
git commit -m "feat: wire web search cli command"
```

### Task 6: Add the new skill document with miaoda parity

**Files:**
- Create: `metainflow-skills/metainflow-web-search/SKILL.md`
- Reference: `miaoda-skills/miaoda-web-search/SKILL.md`

**Step 1: Write the failing test**

Review the reference skill and list the required sections for parity:
- frontmatter
- quick reference table
- command decision tree
- usage examples
- instruction guidance
- common mistakes

Expected failure: no correct `metainflow-web-search` skill exists yet or it still describes provider-native web search.

**Step 2: Verify the gap**

Run: `python - <<'PY'
from pathlib import Path
text = Path('metainflow-skills/metainflow-web-search/SKILL.md').read_text() if Path('metainflow-skills/metainflow-web-search/SKILL.md').exists() else ''
print('provider-native web search' in text)
PY`
Expected: the skill is missing or out of date relative to the revised architecture.

**Step 3: Write minimal implementation**

Create or update `metainflow-skills/metainflow-web-search/SKILL.md` so that:
- outward usage stays aligned with `miaoda-web-search`
- internal dependency wording states search is done by metainflow itself
- summary remains model-backed but not provider-native search-backed

**Step 4: Verify the file exists and reads clearly**

Run: `python - <<'PY'
from pathlib import Path
print(Path('metainflow-skills/metainflow-web-search/SKILL.md').read_text())
PY`
Expected: the skill file exists and includes the expected sections.

**Step 5: Commit**

```bash
git add metainflow-skills/metainflow-web-search/SKILL.md
git commit -m "feat: add web search skill"
```

### Task 7: Update docs for the revised command architecture

**Files:**
- Modify: `README.md`
- Modify: `docs/usage.md`
- Modify: `docs/agent-usage.md`
- Modify: `docs/technical-architecture-plan.md`

**Step 1: Write the failing test**

List the missing docs coverage:
- README command mention
- user-facing usage examples
- agent-facing invocation examples
- architecture doc notes that search is self-implemented and summary is model-backed

Expected failure: current docs still describe provider compatibility constraints instead of the revised owned-search architecture.

**Step 2: Verify the gap**

Run: `rg -n "provider-native|OpenAI-compatible web search|search-summary|web-search" README.md docs/usage.md docs/agent-usage.md docs/technical-architecture-plan.md`
Expected: stale wording exists or coverage is incomplete.

**Step 3: Write minimal implementation**

Update docs so they describe the revised contract accurately.

**Step 4: Verify docs updated**

Run: `rg -n "provider-native|OpenAI-compatible web search|search-summary|web-search" README.md docs/usage.md docs/agent-usage.md docs/technical-architecture-plan.md`
Expected: stale wording removed and intended references present.

**Step 5: Commit**

```bash
git add README.md docs/usage.md docs/agent-usage.md docs/technical-architecture-plan.md
git commit -m "docs: update web search architecture"
```

### Task 8: Run verification suite

**Files:**
- No code changes required unless failures appear

**Step 1: Run focused tests**

Run:

```bash
pytest tests/test_config.py tests/services/test_web_search_search_provider.py tests/services/test_web_search_summary_provider.py tests/services/test_web_search_service.py tests/cli/test_search_summary_json.py tests/test_cli_help.py -q
```

Expected: PASS.

**Step 2: Run broader regression tests**

Run:

```bash
pytest -q
```

Expected: PASS or the same existing skip profile as before.

**Step 3: Fix any failures minimally**

If anything fails, fix the smallest necessary issue, then rerun the affected tests before rerunning the full suite.

**Step 4: Commit final verification fixes if needed**

```bash
git add .
git commit -m "test: finish web search integration"
```

Only create this commit if verification required code changes.
