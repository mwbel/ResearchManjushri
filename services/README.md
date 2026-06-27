# Services

`services/` 用于放置可独立运行或可被多个应用复用的服务模块。

当前不迁移 `LLM Wiki/` 的既有后端代码。后续新增服务时再放入本目录。

建议服务类型：

- `source-ingest-service`: 资料导入、正文抽取、元数据标准化。
- `concept-service`: 候选概念、合并建议、概念页 CRUD。
- `graph-service`: 概念关系、图谱查询、投影重建。
- `review-service`: 人工审核队列、接受/拒绝/修改动作。
- `model-gateway-service`: 多模型调用、路由、成本和日志。

服务必须提供清晰 API，不直接依赖前端页面状态。
