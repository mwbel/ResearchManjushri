# 模块化开发边界

## 总原则

LLM Wiki 作为核心知识编译模块，后续能力通过模块化目录和 API 契约扩展。

不再把所有新功能都直接塞进 `LLM Wiki/webui/app.js` 或 `scripts/wiki_web.py`。当能力会被多个应用使用时，应先定义模块边界。

## 当前层次

```text
应用层
- LLM Wiki Web UI
- Reader Workbench
- 后续管理后台

接口层
- docs/api/llm-wiki-api.md
- 后续 FastAPI/HTTP adapter

领域层
- sources
- concepts
- relations
- reviews
- graphs
- readers

核心实现
- LLM Wiki/scripts/
- LLM Wiki/webui/
- LLM Wiki/raw/
- LLM Wiki/wiki/
```

## 开发规则

1. 新功能先判断是页面能力、服务能力还是领域能力。
2. 页面能力可以放在对应前端，但不得直接定义长期业务状态。
3. 服务能力优先抽象为 API，再由不同应用调用。
4. 领域能力必须明确数据对象、状态流转和错误处理。
5. 对 `raw/`、`wiki/` 的写操作必须通过核心后端或明确脚本执行。

## 不迁移的内容

当前不移动：

- `LLM Wiki/scripts/wiki_web.py`
- `LLM Wiki/webui/`
- `LLM Wiki/raw/`
- `LLM Wiki/wiki/`

这些内容继续作为现有 MVP 核心运行。
