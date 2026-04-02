"""Minimal tests for MVP tools."""

from __future__ import annotations

from importlib.util import find_spec
from pathlib import Path
import tempfile
import unittest
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from test_case_writing_crew.schemas import GateCriterion, TestCase, TestPoint  # noqa: E402
from test_case_writing_crew.tools.coverage_builder import build_coverage_matrix  # noqa: E402
from test_case_writing_crew.tools.csv_exporter import (  # noqa: E402
    export_list_to_csv,
    export_mvp_csv_bundle,
)
from test_case_writing_crew.tools.document_loader import load_documents  # noqa: E402
from test_case_writing_crew.tools.excel_exporter import export_mvp_excel  # noqa: E402
from test_case_writing_crew.tools.knowledge_retriever import retrieve_knowledge  # noqa: E402


class ToolsMVPTest(unittest.TestCase):
    """MVP tool smoke tests."""

    def test_document_loader_supports_required_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.md").write_text("# title\ncontent", encoding="utf-8")
            (root / "b.txt").write_text("plain text", encoding="utf-8")
            (root / "c.csv").write_text("id,name\n1,alpha\n2,beta\n", encoding="utf-8")
            (root / "d.yaml").write_text("k: v\n", encoding="utf-8")
            (root / "e.json").write_text('{"k": "v"}', encoding="utf-8")

            docs = load_documents(
                [root / "a.md", root / "b.txt", root / "c.csv", root / "d.yaml", root / "e.json"]
            )
            self.assertEqual(len(docs), 5)
            self.assertEqual(docs[0].source_name, "a.md")
            self.assertIn("line_count", docs[0].metadata)

    def test_knowledge_retriever_keyword_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            knowledge_root = Path(tmp) / "knowledge"
            (knowledge_root / "defect_patterns").mkdir(parents=True)
            (knowledge_root / "domain_rules").mkdir(parents=True)
            (knowledge_root / "defect_patterns" / "pattern.md").write_text(
                "Login defect pattern: lockout missing after failed attempts.",
                encoding="utf-8",
            )
            (knowledge_root / "domain_rules" / "rules.txt").write_text(
                "Role-based access control is required for admin and operator.",
                encoding="utf-8",
            )

            matches = retrieve_knowledge(
                query="lockout failed",
                base_dir=knowledge_root,
                category="defect_patterns",
            )
            self.assertGreaterEqual(len(matches), 1)
            self.assertEqual(matches[0].category, "defect_patterns")

    def test_coverage_builder(self) -> None:
        test_points = [
            TestPoint(
                test_point_id="TP-1",
                module="auth",
                sub_module="login",
                requirement_id="REQ-1",
                test_dimension="functional",
                title="Login success path",
                description="Validate successful login.",
            )
        ]
        test_cases = [
            TestCase(
                case_id="TC-1",
                module="auth",
                sub_module="login",
                test_point_id="TP-1",
                requirement_id="REQ-1",
                title="Admin can login",
                preconditions=["Admin account exists"],
                steps=["Open login", "Input credentials", "Submit"],
                expected_result="Login succeeds.",
            )
        ]
        requirements = [{"requirement_id": "REQ-1", "requirement_desc": "System supports login"}]

        matrix = build_coverage_matrix(test_points, test_cases, requirements=requirements)
        self.assertEqual(len(matrix), 1)
        self.assertEqual(matrix[0].coverage_status, "covered")

    def test_csv_exporters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "out"
            test_points = [
                TestPoint(
                    test_point_id="TP-1",
                    module="auth",
                    sub_module="login",
                    requirement_id="REQ-1",
                    test_dimension="functional",
                    title="login",
                    description="desc",
                )
            ]
            test_cases = [
                TestCase(
                    case_id="TC-1",
                    module="auth",
                    sub_module="login",
                    test_point_id="TP-1",
                    requirement_id="REQ-1",
                    title="case",
                    preconditions=["p"],
                    steps=["s1"],
                    expected_result="ok",
                )
            ]
            gates = [
                GateCriterion(
                    criterion_id="GC-1",
                    criterion_type="entry",
                    category="functional",
                    description="must map requirements",
                    threshold="100%",
                    mandatory=True,
                )
            ]

            bundle = export_mvp_csv_bundle(test_points, test_cases, gates, output_dir)
            self.assertTrue(bundle["test_points"].exists())
            self.assertTrue(bundle["test_cases"].exists())
            self.assertTrue(bundle["quality_gates"].exists())

            single_path = export_list_to_csv(test_points, output_dir / "single.csv")
            self.assertTrue(single_path.exists())

    @unittest.skipIf(find_spec("openpyxl") is None, "openpyxl not installed")
    def test_excel_exporter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_file = Path(tmp) / "result.xlsx"
            test_points = [
                TestPoint(
                    test_point_id="TP-1",
                    module="auth",
                    sub_module="login",
                    requirement_id="REQ-1",
                    test_dimension="functional",
                    title="login",
                    description="desc",
                )
            ]
            test_cases = [
                TestCase(
                    case_id="TC-1",
                    module="auth",
                    sub_module="login",
                    test_point_id="TP-1",
                    requirement_id="REQ-1",
                    title="case",
                    preconditions=["p"],
                    steps=["s1"],
                    expected_result="ok",
                )
            ]
            gates = [
                GateCriterion(
                    criterion_id="GC-1",
                    criterion_type="exit",
                    category="stability",
                    description="no critical defects",
                    threshold="0",
                    mandatory=True,
                )
            ]

            path = export_mvp_excel(test_points, test_cases, gates, output_file)
            self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
