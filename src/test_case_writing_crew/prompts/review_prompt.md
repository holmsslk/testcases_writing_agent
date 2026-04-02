# Review Prompt (MVP)

只输出 JSON，且仅包含键：
- `review_result`

约束：
- 使用简体中文（接口名/字段名/错误码可保留英文）。
- `comments` 最多 8 条，仅保留最关键问题。
- 避免重复问题和长篇评审报告。
- 不允许新增顶层键，不允许 markdown 包裹，不允许额外 prose。
