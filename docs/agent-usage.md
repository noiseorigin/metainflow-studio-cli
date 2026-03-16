# metainflow-studio-cli Agent Usage

本文件给 agent 和开发者使用，目标是两件事：

- 快速调用 `metainflow-studio-cli`
- 快速开发和验证新的 metainflow 能力与 skill

## 1. 这个项目是什么

当前 `metainflow-studio-cli` 是一个 Python CLI 工具箱。

现阶段已实现的主能力：

- `parse-doc`
- `search-summary`
- `web-crawl`

对应 skill：

- `metainflow-doc-parse`
- `metainflow-web-search`
- `metainflow-web-fetch`

当前支持的文档类型：

- `.pdf`
- `.doc`
- `.docx`
- `.pptx`
- `.xls`
- `.xlsx`
- `.csv`
- `.txt`
- `.md`
- `.html`

---

## 2. 首次上手

在项目根目录执行：

```bash
python -m pip install -e '.[dev]'
python -m playwright install chromium
hash -r
```

验证 CLI 已安装：

```bash
which metainflow
metainflow --help
metainflow parse-doc --help
metainflow search-summary --help
metainflow web-crawl --help
```

## 3. Agent 如何调用这个工具

### 方式 A：直接调用 CLI

```bash
metainflow parse-doc --file ./tests/integration/samples/Assignment1.docx --output json
metainflow search-summary --query "React 19 新特性" --output json
metainflow web-crawl --url https://example.com --output json
```

如果 shell 里没有 `metainflow`，临时改用：

```bash
python -m metainflow_studio_cli.main parse-doc --file ./tests/integration/samples/Assignment1.docx --output json
python -m metainflow_studio_cli.main search-summary --query "React 19 新特性" --output json
python -m metainflow_studio_cli.main web-crawl --url https://example.com --output json
```

### 方式 B：通过 skill 调用

在仓库根目录挂载到 OpenCode 用户技能目录：

```bash
ln -sfn "$(pwd)/metainflow-skills/metainflow-doc-parse" "$HOME/.agents/skills/metainflow-doc-parse"
ln -sfn "$(pwd)/metainflow-skills/metainflow-web-search" "$HOME/.agents/skills/metainflow-web-search"
ln -sfn "$(pwd)/metainflow-skills/metainflow-web-fetch" "$HOME/.agents/skills/metainflow-web-fetch"
```

验证挂载：

```bash
ls -l "$HOME/.agents/skills/metainflow-doc-parse"
ls -l "$HOME/.agents/skills/metainflow-web-search"
ls -l "$HOME/.agents/skills/metainflow-web-fetch"
```

## 4. 关键配置说明

### `search-summary`

当前默认搜索策略是：

1. 智谱 provider 搜索
2. SearXNG fallback
3. 百度 Playwright fallback

如果想启用智谱主链路，推荐显式设置：

```bash
export PROVIDER_BASE_URL="https://open.bigmodel.cn/api/paas/v4"
export PROVIDER_API_KEY="your-api-key"
export WEB_SEARCH_BACKEND="auto"
export SEARCH_PROVIDER_ENGINE="search_pro"
export SEARCH_RESULT_COUNT="10"
```

如果总结阶段要走独立端点，可额外设置：

```bash
export SUMMARY_BASE_URL="https://your-summary-endpoint/v1"
export SUMMARY_API_KEY="your-summary-api-key"
export SUMMARY_MODEL="glm-4-flash"
```

### `web-crawl`

`web-crawl` 用 Crawl4AI 抓取页面正文，再按需做总结。常用配置：

```bash
export PROVIDER_API_KEY="your-api-key"
export PROVIDER_MODEL_WEB_FETCH="gpt-4.1-mini"
export METAINFLOW_WEB_FETCH_VERIFY_SSL="1"
```

## 5. 本地更新后的正确步骤

```bash
python -m pip install -e '.[dev]'
python -m playwright install chromium
hash -r
pytest -q
```

如果只想验证真实样本矩阵：

```bash
METAINFLOW_RUN_SAMPLE_MATRIX=1 pytest -q tests/integration/test_real_sample_matrix.py
```

## 6. 开发新能力时的建议流程

通常会改这些位置：

- `metainflow_studio_cli/main.py`
- `metainflow_studio_cli/core/`
- `metainflow_studio_cli/services/`
- `tests/`
- `metainflow-skills/<skill-name>/SKILL.md`

建议顺序：

1. 先写测试
2. 再写 service 逻辑
3. 最后接 CLI 命令
4. 再补 skill 文档与挂载验证
