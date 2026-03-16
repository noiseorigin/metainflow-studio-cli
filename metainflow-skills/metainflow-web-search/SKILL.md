---
name: metainflow-web-search
description: "Use when user needs to search the web for information by keywords. Provides search-summary command for web search with AI-generated summaries. 触发词：搜索, 网页搜索, 搜一下, 查一下, web search, 搜索摘要, 查资料, 搜索引擎, search"
---

# Web Search

通过 `metainflow search-summary` 按关键词搜索互联网信息，由 AI 自动总结。

搜索结果由 `metainflow-studio-cli` 自己获取，当前默认搜索源是 Playwright 驱动的百度搜索，配置模型只负责总结。

## Quick Reference

| 参数 | 说明 | 必需 | 默认值 |
|------|------|------|--------|
| `--query` | 搜索关键词 | 是 | - |
| `--instruction` | AI 处理指令 | 否 | - |
| `--output, -o` | 输出格式: text/json | 否 | text |

## 命令选择决策树

```
用户想获取互联网信息
├─ 有具体 URL → 未来使用 metainflow web-crawl
├─ 无具体 URL，需搜索 → metainflow search-summary
└─ 先搜索再深入 → search-summary 获取 URL → 再用未来的 web-crawl 提取详情
```

## 使用示例

```bash
# 按关键词搜索
metainflow search-summary --query "React 19 新特性" --instruction "按功能分类整理，标注稳定性状态"

# 搜索并获取 JSON 输出
metainflow search-summary --query "ByteDance 开源项目" --output json
```

## --instruction 编写指南

| 场景 | instruction 示例 |
|------|-----------------|
| 按条件筛选 | `"只保留 2024 年之后发布的内容"` |
| 对比分析 | `"对比各方案的优缺点，给出推荐"` |
| 翻译总结 | `"用中文总结主要观点"` |
| 不指定（默认） | AI 自动总结主要信息 |

## Common Mistakes

| 错误 | 正确做法 |
|------|----------|
| 无具体 URL 时等未来 `metainflow web-crawl` | 无 URL 用 `metainflow search-summary`，有 URL 时再走未来 `web-crawl` |
| 把 `search-summary` 当成 provider-native web search | 当前搜索由 `metainflow-studio-cli` 自己完成，模型只负责总结 |
| `--instruction` 过于笼统（如"总结一下"） | 明确指定提取目标、输出格式、筛选条件 |
| 搜索关键词过长且无重点 | 提炼核心关键词，保持精简 |
| 需要后续程序处理结果但未加 `--output json` | 需要解析结果时始终加 `--output json` |
| 命令失败后不检查退出码 | 退出码 `1/2/3` 表示不同失败类型，检查参数和网络后重试 |
