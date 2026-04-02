# 端到端真实验收运行说明（MVP）

本文档用于一次真实验收：验证项目是否可稳定输出可用的中文测试资产（测试点、测试用例、评审结果、准入准出标准、CSV/XLSX）。

## 1. 输入文件准备

推荐直接使用仓库内样例（软硬件一体场景）：

- `examples/sample_prd.md`
- `examples/sample_api.yaml`
- `examples/sample_requirement_table.csv`

人工审核文件：

- `examples/human_reviews/requirements_review.json`
- `examples/human_reviews/release_review.json`

说明：

- `requirements_review.json` 中 `requires_regeneration` 默认为 `false` 时，Flow 会复用第一次 Crew 结果，避免无意义二次 kickoff。
- 若你确认本次人工补洞会实质影响测试生成，可将其设置为 `true`。

## 2. 环境变量与依赖

至少确保：

- 已安装依赖（`crewai`、`pyyaml`，可选 `openpyxl`）
- `.env` 中有可用模型配置（至少 `OPENAI_API_KEY`）

建议最小 `.env` 示例：

```env
OPENAI_API_KEY=你的密钥
MODEL=gpt-4o-mini
```

如需导出 Excel，请确保安装：

```bash
uv add openpyxl
```

## 3. 推荐验收命令

在项目根目录执行：

```bash
cd /home/holms/crews/test_case_writing_crew
PYTHONPATH=src uv run python -m test_case_writing_crew.main \
  --mode flow \
  --input /home/holms/crews/test_case_writing_crew/examples/sample_prd.md \
  --input /home/holms/crews/test_case_writing_crew/examples/sample_api.yaml \
  --input /home/holms/crews/test_case_writing_crew/examples/sample_requirement_table.csv \
  --review-mode file \
  --human-review-dir /home/holms/crews/test_case_writing_crew/examples/human_reviews \
  --outputs-interim-dir /home/holms/crews/test_case_writing_crew/outputs/interim \
  --outputs-final-dir /home/holms/crews/test_case_writing_crew/outputs/final
```

## 4. 人工审核说明（file 模式）

### 4.1 需求补洞确认

文件：`examples/human_reviews/requirements_review.json`

关键字段：

- `approved`: 是否通过需求审核
- `requires_regeneration`: 是否需要重新生成（默认 `false`）
- `clarified_context`: 补充上下文

### 4.2 最终发布确认

文件：`examples/human_reviews/release_review.json`

关键字段：

- `decision`: `approve | rework | reject`

## 5. 预期输出物

中间结果目录：

- `outputs/interim/`（阶段数据与状态快照）

最终结果目录：

- `outputs/final/testcase_mvp_testpoints.csv`
- `outputs/final/testcase_mvp_testcases.csv`
- `outputs/final/testcase_mvp_qualitygates.csv`
- `outputs/final/testcase_mvp.xlsx`（安装 `openpyxl` 时）
- `outputs/final/flow_state.json`

## 6. 如何判断本次运行成功

满足以下条件即可判定一次验收运行成功：

1. 命令执行结束，进程退出，无持续挂起。
2. `outputs/final/flow_state.json` 存在，且 `release_decision=approve`。
3. `export_paths` 中存在 CSV 路径；安装了 `openpyxl` 时存在 Excel 路径。
4. `test_points`、`test_cases`、`quality_gates` 均有内容。
5. 输出自然语言内容以简体中文为主，可直接用于中文测试团队评审。

## 7. 验收清单

请按下述清单逐条勾选：

- [ ] 已生成中文测试点（`testcase_mvp_testpoints.csv`）。
- [ ] 已生成中文测试用例（`testcase_mvp_testcases.csv`）。
- [ ] 已输出准入准出标准（`testcase_mvp_qualitygates.csv`）。
- [ ] 已提出高价值澄清问题（查看 `flow_state.json` 的 `clarification_questions`）。
- [ ] 输出条数受控（澄清问题/测试点/用例/评审意见/门禁条目未明显失控）。
- [ ] 已导出 CSV，且在安装 `openpyxl` 时已导出 XLSX。
- [ ] 结果中无明显英文残留（允许接口路径/字段名/错误码等必要英文）。
- [ ] 用例无明显重复（标题、步骤、预期结果无大面积重复）。

补充：你也可以使用独立清单文件 [acceptance_checklist.md](/home/holms/crews/test_case_writing_crew/docs/acceptance_checklist.md) 做签核。
