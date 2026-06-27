# Domains

`domains/` 用于记录领域模块边界。

领域模块不是 `app/llm-wiki/wiki/domains/` 的替代品。这里描述软件架构里的业务领域；`app/llm-wiki/wiki/domains/` 仍然是知识库里的学科页面。

建议领域：

- `sources`: 原始资料、资料卡、上传文件、正文抽取。
- `concepts`: 概念候选、概念页、别名、定义、合并。
- `relations`: 概念关系、证据、关系类型。
- `reviews`: 待整理概念、待补资料、人工审核动作。
- `graphs`: 学科图谱、节点/边查询、图谱投影。
- `readers`: 阅读器、分页正文、解释、批注。

每个领域后续应补充：

1. 数据对象。
2. API 输入输出。
3. 状态流转。
4. 与前端 app、管理后台、后端、数据库的责任边界。

建议与 API 契约联动的补充格式：

- `request_schema`: 入参字段、字段类型、默认值
- `response_schema`: 响应字段、错误场景
- `state_machine`: 状态变化与可达边界
- `api_owner`: 负责团队/接口联系人
