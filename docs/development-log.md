# metainflow-studio-cli 开发日志

## 2026-03-14

### 阶段目标
- 初始化 `metainflow-studio-cli` 项目结构。
- 优先实现 `parse-doc` 命令。
- 支持文档格式矩阵：`.pdf .doc .docx .pptx .xls .xlsx .csv .txt .md .html`。
- 建立真实样本验证基线。

### 已完成内容
- 创建项目基础文件：`pyproject.toml`、包入口、测试目录。
- 实现 CLI 命令：`parse-doc --file --output text|json`。
- 实现 `PROVIDER_*` 配置读取基础：
  - `PROVIDER_BASE_URL`
  - `PROVIDER_API_KEY`
  - `PROVIDER_TIMEOUT_SECONDS`
  - `PROVIDER_MAX_RETRIES`
  - `PROVIDER_MODEL_DOC_PARSE`
- 实现解析服务主链路（按扩展名分发）：
  - 文本：`.txt`, `.md`
  - 表格：`.csv`, `.xls`, `.xlsx`
  - Office：`.docx`, `.pptx`, `.doc`（通过 soffice 转换）
  - 网页：`.html`
  - PDF：文本抽取 + OCR 兜底
- 实现 URL 输入下载能力（HTTP/HTTPS）。
- 建立统一输出 envelope：`success/data/meta/error`。
- 实现错误码映射：
  - `0` 成功
  - `1` 处理失败
  - `2` 参数/校验失败
  - `3` 外部依赖或网络失败
- 在 `feat/web-search` worktree 中实现 `search-summary` 的独立开发分支。
- 将 web search 主链路改为 `Playwright + 百度搜索 + 普通模型总结`。
- 将百度入口策略优化为：`www.baidu.com` 主路径，`m.baidu.com` 兜底。
- 将浏览器层升级为 `undetected-playwright`。
- 实现 `playwright_search_provider`，并修复真实百度页面上的三个关键问题：
  - 结果节点实际为 `ElementHandle`，不能按 `Locator` 假设处理
  - 摘要内容位于 `[data-sanssr-cmpt="card/www-summary"]`
  - `.result-op` 不是无结果标记，不能提前返回空结果

### 测试与验证结果
- 单元/服务测试：`pytest -q` 结果 `55 passed, 2 skipped`。
- 样本矩阵校验：
  - 命令：`METAINFLOW_RUN_SAMPLE_MATRIX=1 pytest -q tests/integration/test_real_sample_matrix.py`
  - 结果：`2 passed`
- 真实样本逐个命令验证（`parse-doc --output json`）：
  - 通过：`pdf/doc/docx/pptx/xls/xlsx/csv/txt/md/html`
  - 失败：`doc`（在缺少 `soffice` 的环境中）

- `feat/web-search` worktree 聚焦测试：`24 passed`
- `feat/web-search` worktree 全量测试：`40 passed, 1 skipped`
- `feat/web-search` 真实联调：
  - `python -m metainflow_studio_cli.main search-summary --query "React 19 新特性" --output json`
  - 结果：Playwright 百度搜索返回非空结果，普通模型总结成功
- 百度入口稳定性验证：
  - `www.baidu.com`：连续 5/5 次返回结果页
  - `m.baidu.com`：0/5 次拿到可用结果，其中多次直接进入验证页

### 当前阶段进展（2026-03-14 晚）
- `.xls -> .xlsx` 转换链路已经接入，并加入真实 `.xls` 样本回归。
- `.xlsx` 解析已支持按坐标落位、保留稀疏列、展开 merged cells。
- `.doc` / `.xls` 的 `source.resolved_path` 与 `source.file_type` 已保留原始输入信息。
- `soffice` 偶发返回成功但产物延迟出现的问题已通过“等待可读产物 + 一次重试”缓解。
- 已完成复杂模板热点分析，并产出 sheet 内区域切分的实现计划。
- `metainflow-doc-parse` skill 已补充 `.xls` 与 merged cells 的行为说明。

### 当前已知问题
- `.doc` / `.xls` 解析仍依赖 LibreOffice：若系统无 `soffice`，会返回错误。
- 复杂 Excel 模板虽然已减少 merge cell 数据丢失，但仍无法完整保留原始视觉结构。
- sheet 内区域切分尚未正式落地，复杂模板的短语级文本丢失率仍有进一步优化空间。
- 当前 `tables` 仍是扁平 rows 输出，尚未暴露 sheet / region 边界元数据。
- Playwright 搜索链路仍依赖浏览器环境与百度页面结构。
- 当前搜索结果 URL 仍是百度跳转链接，未解析到最终目标地址。
- `m.baidu.com` 在当前服务器环境下不稳定，只适合作为 fallback。

### 下一步计划
- 在 Ubuntu 服务器安装并验证系统依赖：`libreoffice`、`tesseract-ocr`、`poppler-utils` 等。
- 优先优化复杂模板中的长文本保真，减少单元格内容被拆散后无法回拼的问题。
- 为 sheet 内区域切分增加更稳健的规则，提升复杂模板的表块识别准确性。
- 评估是否为 `tables` 增加 `sheet` / `region` / `merge metadata`，方便后处理和调试。
- 持续补充真实样本端到端断言，不只检查扩展名覆盖，还检查输出字段和内容质量。
- 为 Playwright 百度搜索补充跳转链接解析、质量过滤和多源 fallback。
