# API Response Envelope

后续新接口建议统一返回：

```json
{
  "ok": true,
  "data": {},
  "error": null,
  "meta": {}
}
```

失败时：

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "文件不存在"
  },
  "meta": {}
}
```

## 常用错误码

- `FILE_NOT_FOUND`: 本地文件不存在。
- `VALIDATION_ERROR`: 输入字段不完整或格式错误。
- `DOMAIN_NOT_ALLOWED`: 学科不在允许列表。
- `SOURCE_NOT_FOUND`: 资料不存在。
- `CONCEPT_NOT_FOUND`: 概念不存在。
- `REVIEW_ALREADY_RESOLVED`: 审核任务已处理。
- `INTERNAL_ERROR`: 未分类服务错误。
