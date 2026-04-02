# Test Case Writing Crew MVP

里程碑封板说明见：[MVP_DONE.md](/home/holms/crews/test_case_writing_crew/MVP_DONE.md)

## 1. 项目简介
这是一个面向“软硬件一体系统”的测试用例生成 MVP。
当前仓库已经完成 **Flow + Crew 一体化**：
- **Flow 是唯一推荐主入口**（负责编排、人工审核、回退、导出）
- **Crew 是核心协作引擎**（负责结构化生成需求摘要、测试点、测试用例、评审结果、质量门禁）
- 主链路是：**Flow 调 Crew，再由 Flow 消费结果并完成发布流程**
- Crew 主 `run()` 默认由 **真实 CrewAI `crew().kickoff()`** 驱动，再经标准化层转换为 `CrewExecutionResult`
- `execute_pipeline_structured(...)` 仅作为 fallback/debug 兼容路径
- 默认中文输出策略：除系统字段名外，测试点/测试用例/评审/门禁等自然语言内容默认使用简体中文

## 2. 当前架构（与代码一致）
### 2.1 角色分工
- Flow（`src/test_case_writing_crew/flows/testcase_generation_flow.py`）负责：
  - 输入接入（`ingest_documents`）
  - 人工审核节点 1（需求补洞确认）
  - 调用 Crew 并同步 state
  - 人工审核节点 2（最终发布确认）
  - 回退控制
  - CSV / Excel 导出
- Crew（`src/test_case_writing_crew/crews/test_design_crew.py` + `runner.py`）负责：
  - `requirement_summary`
  - `clarification_questions`
  - `test_points`
  - `test_cases`
  - `review_result`
  - `quality_gates`

### 2.2 一体化接口
Flow 通过稳定接口调用 Crew：
- `TestDesignCrewRunner`
- `TestDesignCrewInput`
- `TestDesignCrewRunner.run(...)` 默认调用 `TestDesignCrew.run(...)`（kickoff-first）

## 3. 主链路步骤图（文字版）
1. `ingest_documents`
2. `analyze_requirements`（Flow 调 Crew，获取结构化结果并写入 state）
3. `human_review_requirements`（人工审核节点 1）
4. `generate_test_points`（使用 Crew 结果）
5. `generate_test_cases`（使用 Crew 结果，可重跑）
6. `review_test_assets`（使用 Crew 评审结果）
7. `generate_quality_gates`（使用 Crew 门禁结果）
8. `human_release_review`（人工审核节点 2）
9. `export_outputs`（从统一 state 导出 CSV/Excel）

回退机制：
- 审核节点 1 不通过：回到需求分析阶段
- 审核节点 2 选择 `rework`：回到测试用例生成阶段

## 4. 目录结构
```text
test_case_writing_crew/
├── examples/
│   ├── sample_prd.md
│   ├── sample_api.yaml
│   ├── sample_requirement_table.csv
│   ├── human_reviews/
│   │   ├── requirements_review.json
│   │   └── release_review.json
│   ├── crew_runner_example.py          # debug only
│   └── verify_integration.py           # E2E 验证脚本
├── knowledge/
├── outputs/
│   ├── interim/
│   └── final/
├── src/test_case_writing_crew/
│   ├── main.py                         # 推荐主入口
│   ├── flows/
│   ├── crews/
│   ├── agents/
│   ├── tasks/
│   ├── schemas/
│   ├── tools/
│   ├── config/
│   └── prompts/
└── tests/
    ├── test_flow_mvp.py
    └── test_flow_crew_integration_e2e.py
```

## 5. 运行前准备
- Python：建议 `>=3.10`
- 建议使用 `uv`
- 依赖：`crewai`、`pyyaml`，可选 `openpyxl`（Excel 导出）

示例：
```bash
uv add crewai
uv add pyyaml
uv add openpyxl
```

## 6. 推荐运行方式（End-to-End）
推荐入口：`main.py`，默认 `--mode flow`。

```bash
PYTHONPATH=src python3 -m test_case_writing_crew.main \
  --mode flow \
  --input examples/sample_prd.md \
  --input examples/sample_api.yaml \
  --input examples/sample_requirement_table.csv \
  --review-mode file \
  --human-review-dir examples/human_reviews \
  --outputs-interim-dir outputs/interim \
  --outputs-final-dir outputs/final
```

最简命令（使用默认样例与默认目录）：
```bash
PYTHONPATH=src python3 -m test_case_writing_crew.main
```

## 7. 调试运行方式
### 7.1 Crew 调试（debug only）
只跑 Crew，不跑人工审核与 Flow 回退：
```bash
PYTHONPATH=src python3 -m test_case_writing_crew.main \
  --mode crew-debug \
  --input examples/sample_prd.md
```

### 7.2 Python 调试（not recommended for end-to-end execution）
- 直接在脚本中 new `TestcaseGenerationFlow` / `TestDesignCrewRunner` 仅用于开发调试。
- `examples/crew_runner_example.py`：**debug only**。
- `execute_pipeline_structured(...)`：**fallback/debug only**（非默认事实来源）。

## 8. 人工审核节点操作说明
支持两种审核模式：
- `review_mode=file`（推荐）
- `review_mode=cli`

### 节点 1：需求补洞确认
文件：`examples/human_reviews/requirements_review.json`
- `approved`: `true/false`
- `requires_regeneration`: `true/false`（可选，默认 `false`）
- `clarified_context`: 补充上下文（如版本、模块）

说明：
- 默认 `requires_regeneration=false`，Flow 会复用第一次 Crew 结果，不会触发无意义的第二次完整 kickoff。
- 仅当 `requires_regeneration=true` 且 `clarified_context` 包含会实质影响生成的关键变更时，才会失效缓存并重新调用 Crew。

### 节点 2：最终发布确认
文件：`examples/human_reviews/release_review.json`
- `decision`: `approve | rework | reject`

## 9. 输出文件说明
### 9.1 中间产物
目录：`outputs/interim/`
- 阶段数据（`01_...` 到 `09_...`）
- 每阶段状态快照（`*_state.json`）

### 9.2 最终产物
目录：`outputs/final/`
- `testcase_mvp_testpoints.csv`
- `testcase_mvp_testcases.csv`
- `testcase_mvp_qualitygates.csv`
- `testcase_mvp.xlsx`（安装 `openpyxl` 时）
- `flow_state.json`

说明：最终导出来自统一 `Flow state`，不是多个分散来源。

## 9.1 中文输出规范化策略
在导出 CSV / Excel 之前，系统会自动执行一次中文文案规范化（不改变业务语义）：
- 标题规范：优先收敛为 `【模块】验证……`
- 步骤规范：统一为中文编号动作描述（如 `1）... 2）...`）
- 预期结果规范：尽量收敛为可观察、可验证表达
- 评审意见与门禁说明：统一中文句式和标点

不会被改写的关键内容：
- API 路径（如 `POST /device/start`）
- 协议/字段名（如 `device_id`）
- 错误码（如 `TIMEOUT_ERROR`）
- 枚举值、变量名、明确产品英文按钮/菜单名

## 10. 端到端验证方式
验收运行说明文档：
- [acceptance_run_guide.md](/home/holms/crews/test_case_writing_crew/docs/acceptance_run_guide.md)
- [acceptance_checklist.md](/home/holms/crews/test_case_writing_crew/docs/acceptance_checklist.md)

### 10.1 自动化验证（推荐）
```bash
PYTHONPATH=src uv run python -m unittest tests/test_flow_crew_integration_e2e.py
```

### 10.2 手动验证脚本
```bash
PYTHONPATH=src uv run python examples/verify_integration.py
```

验证成功时至少可看到：
- `test_points`
- `test_cases`
- `quality_gates`
- 最终 CSV 路径（`export_paths`）

## 11. 入口状态标记
- `python -m test_case_writing_crew.main --mode flow`：**recommended**
- `python -m test_case_writing_crew.main --mode crew-debug`：**debug only**
- 直接调用零散任务/手动拼链路：**not recommended for end-to-end execution**

## 12. 当前已知限制
- 知识检索为本地关键词匹配（无向量库）。
- 目前为 MVP 规则化生成与评审，不是生产级全自动闭环。

## 13. 最终改造总结
### 已完成的一体化能力
- Flow 与 Crew 已打通，主链路是 `Flow -> Crew -> Flow`。
- Flow state 与 Crew 结构化输出字段已统一。
- 两个人工审核节点可落地（文件/CLI）。
- 回退机制可用（需求补洞回退、发布 rework 回退）。
- 导出统一从 state 生成，CSV/Excel 可用。
- 已有真实 E2E 验证（测试 + 脚本）。

### 非阻塞优化项
1. 清理 CrewAI YAML 配置路径 warning（将配置路径对齐到当前目录结构）。
2. 在 README 增加一键脚本（如 `scripts/run_demo.sh`）进一步降低首次运行成本。
3. 将更多中间数据校验前置到 schema 层（增强错误提示）。
4. 增加更多“回退分支”测试用例（如 release `rework` 多轮验证）。
