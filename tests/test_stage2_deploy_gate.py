import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "run_stage2_deploy_gate.py"
SPEC = importlib.util.spec_from_file_location("run_stage2_deploy_gate", MODULE_PATH)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def validation_for(row_count):
    return {
        "metrics": {
            "stage1Rows": row_count,
            "stage2Rows": row_count,
            "candidateRows": row_count,
            "removedFromStage1": 0,
        },
        "stateCounts": {"stage2_approved": row_count},
        "issueCounts": {},
        "blockingIssueCounts": {},
        "severityCounts": {},
    }


def candidate(job_key="job-1", change_hash="hash-1", **overrides):
    row = {
        "공고키": job_key,
        "변경해시": change_hash,
        "검증상태": "approved",
        "검증우선순위": "pass",
        "이슈코드": "stage2_approved",
        "stage1_분류직무": "인공지능 엔지니어",
        "stage2_분류직무": "인공지능 엔지니어",
        "stage1_직무초점": "모델 서빙",
        "stage2_직무초점": "모델 서빙",
        "stage1_핵심기술": "Python, PyTorch",
        "stage2_핵심기술": "Python, PyTorch",
        "stage1_구분요약": "모델 서빙 플랫폼 개발",
        "stage2_구분요약": "모델 서빙 플랫폼 개발",
        "회사명_표시": "테스트회사",
        "공고제목_표시": "AI Engineer",
        "공고URL": "https://example.test/job",
        "최종발견시각": "2026-04-12T00:00:00Z",
        "승인여부": "승인",
        "검증메모": "",
    }
    row.update(overrides)
    return row


class Stage2DeployGateIntegrityTests(unittest.TestCase):
    def report_for(self, rows):
        deploy_rows = [gate.build_deploy_row(row) for row in rows if gate.row_is_deployable(row)]
        return gate.build_gate_report(validation_for(len(rows)), rows, deploy_rows)

    def test_happy_path_passes(self):
        rows = [
            candidate("job-1", "hash-1"),
            candidate("job-2", "hash-2", stage2_분류직무="데이터 사이언티스트"),
        ]

        report = self.report_for(rows)

        self.assertTrue(report["passed"])
        self.assertNotIn("candidateKeysUnique", report["blockers"])
        self.assertNotIn("deployFieldsComplete", report["blockers"])

    def test_duplicate_candidate_key_blocks_gate(self):
        rows = [
            candidate("job-1", "hash-1"),
            candidate("job-1", "hash-2"),
        ]

        report = self.report_for(rows)

        self.assertFalse(report["passed"])
        self.assertIn("candidateKeysUnique", report["blockers"])
        self.assertEqual(report["metrics"]["duplicateCandidateKeyRows"], 2)

    def test_missing_deploy_field_blocks_gate(self):
        rows = [
            candidate("job-1", "hash-1", stage1_직무초점="", stage2_직무초점=""),
        ]

        report = self.report_for(rows)

        self.assertFalse(report["passed"])
        self.assertIn("deployFieldsComplete", report["blockers"])
        self.assertEqual(report["metrics"]["deployMissingRequiredFieldRows"], 1)

    def test_invalid_deploy_role_blocks_gate(self):
        rows = [
            candidate("job-1", "hash-1", stage1_분류직무="마케터", stage2_분류직무="마케터"),
        ]

        report = self.report_for(rows)

        self.assertFalse(report["passed"])
        self.assertIn("deployRolesAllowed", report["blockers"])
        self.assertEqual(report["metrics"]["deployInvalidRoleRows"], 1)


if __name__ == "__main__":
    unittest.main()
