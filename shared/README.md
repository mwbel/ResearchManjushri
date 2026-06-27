# Shared

`shared/` 用于放置跨模块共享的契约、命名和数据结构说明。

当前先作为文档边界使用，暂不承载运行时代码。

建议后续沉淀：

- 通用 ID 命名规则。
- API response envelope。
- 错误码。
- source / concept / relation / review task 的 schema。
- 前端 app 与管理后台共用的状态枚举。

不要把某个页面专用逻辑放到这里。只有多个模块或多个应用都会用到的内容，才进入 `shared/`。

当前标准入口：

- API 契约：`docs/api/llm-wiki-api.md`
- 共享响应规范：`shared/api-response.md`
