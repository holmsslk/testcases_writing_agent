# Gate Prompt (MVP)

只输出 JSON，且仅包含键：
- `quality_gates`

约束：
- 使用简体中文（接口名/字段名/错误码可保留英文）。
- `entry_criteria` 最多 8 条，`exit_criteria` 最多 8 条。
- 仅输出关键门禁，避免空洞模板化描述。
- 不允许新增顶层键，不允许 markdown 包裹，不允许额外 prose。
