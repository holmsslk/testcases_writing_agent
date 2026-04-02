# Requirement Prompt (MVP)

只输出 JSON，且仅包含键：
- `requirement_summary`

约束：
- 使用简体中文（接口名/字段名/错误码可保留英文）。
- 短输出优先，不要生成报告式长文。
- 不允许新增顶层键，不允许 markdown 包裹，不允许额外总结段落。
- 不要臆造需求，缺失信息仅保留关键事实。
