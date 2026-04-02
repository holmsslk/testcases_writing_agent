# MVP Done - Flow + Crew Integrated Milestone

## 1. 当前已完成能力
- 已完成 Flow 与 Crew 一体化，主链路可运行。
- 输入支持：`md/txt/csv/yaml/yml/json`（通过 document loader）。
- 已实现结构化 schema：
  - `RequirementSummary`
  - `ClarificationQuestion`
  - `TestPoint`
  - `TestCase`
  - `ReviewResult`
  - `EntryExitCriteriaSet`
  - `CrewExecutionResult`
- 工具层已实现：
  - 文档读取（`document_loader`）
  - 本地知识检索（`knowledge_retriever`）
  - 覆盖矩阵（`coverage_builder`）
  - CSV 导出（`csv_exporter`）
  - Excel 导出（`excel_exporter`）
- 两个人工审核节点已可用：
  - 需求补洞确认
  - 最终发布确认
- 回退机制已可用：
  - 需求审核不通过回退
  - 发布审核 `rework` 回退

## 2. 一体化主链路说明
默认事实来源链路：

`Flow -> TestDesignCrewRunner.run() -> TestDesignCrew.run() -> crew().kickoff() -> CrewExecutionResult -> Flow state -> export`

说明：
- Flow 负责编排、审核、回退、导出。
- Crew 负责核心生成（需求、测试点、用例、评审、门禁）。
- `execute_pipeline_structured(...)` 保留为 fallback/debug，不是默认主路径。

## 3. 推荐运行入口
推荐入口（默认完整闭环）：

```bash
PYTHONPATH=src python3 -m test_case_writing_crew.main
```

显式指定 flow 模式：

```bash
PYTHONPATH=src python3 -m test_case_writing_crew.main --mode flow
```

调试入口（debug only）：

```bash
PYTHONPATH=src python3 -m test_case_writing_crew.main --mode crew-debug --input examples/sample_prd.md
```

## 4. 端到端验证方式
自动化验证：

```bash
PYTHONPATH=src uv run python -m unittest tests/test_flow_crew_integration_e2e.py
```

手动验证脚本：

```bash
PYTHONPATH=src uv run python examples/verify_integration.py
```

完整回归：

```bash
PYTHONPATH=src uv run python -m unittest discover -s tests
```

## 5. 当前输出物说明
中间产物目录：
- `outputs/interim/`
- 包含各阶段 `*.json` 与 `*_state.json` 快照

最终产物目录：
- `outputs/final/testcase_mvp_testpoints.csv`
- `outputs/final/testcase_mvp_testcases.csv`
- `outputs/final/testcase_mvp_qualitygates.csv`
- `outputs/final/testcase_mvp.xlsx`（安装 `openpyxl` 时）
- `outputs/final/flow_state.json`

## 6. 当前已知非阻塞优化项
1. 降低 CrewAI kickoff 失败场景（如缺 API key）下的日志噪音。
2. 增加 `release rework` 多轮回退场景测试覆盖。
3. 进一步增强 kickoff 文本解析鲁棒性（更强的结构提取策略）。
4. 增加一键 demo 脚本（如 `scripts/run_demo.sh`）。

## 7. 建议版本号 / Tag
- 建议 Tag：`v0.1.0-mvp`
- 语义：首个可运行、可验证、可导出的 Flow+Crew 一体化 MVP 封板版本。

