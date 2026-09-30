"""Self-test for starter/scripts/trace_check.py and the starter's GitHub config."""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "starter" / "scripts" / "trace_check.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
ALL_REPORTS = ("junit-jest.xml", "junit-pytest.xml", "junit-gotestsum.xml")

LEDGER = """\
# Ledger

## Requirements

### Requirement: LEDGER-1.1 Percentage split sums to 100
### Requirement: LEDGER-2.1 Remainder goes to the payer
### Requirement: LEDGER-5.1 (manual) Expense list scrolls smoothly
"""
SYNC = "### Requirement: SYNC-1.1 Offline edits survive restart\n"


def trace(specs, reports=ALL_REPORTS, extra_reports=None):
    """Run trace_check.py over the given spec files and reports; return (exit code, output)."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for rel, text in specs.items():
            path = tmp / "specs" / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        (tmp / "reports").mkdir()
        for name in reports:
            shutil.copy(FIXTURES / name, tmp / "reports" / name)
        for name, text in (extra_reports or {}).items():
            (tmp / "reports" / name).write_text(text, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--specs", str(tmp / "specs"), "--reports", str(tmp / "reports")],
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stdout + result.stderr


class TraceCheck(unittest.TestCase):
    def test_passing_tests_from_any_runner_cover_their_requirements(self):
        code, out = trace({"ledger/spec.md": LEDGER, "sync/spec.md": SYNC})
        self.assertEqual(code, 0, out)
        self.assertIn("manual (verify by hand before release):\n  LEDGER-5.1", out)

    def test_skipped_and_failing_tests_are_not_evidence(self):
        spec = LEDGER + "### Requirement: LEDGER-3.1 Shares are rounded\n### Requirement: LEDGER-4.1 At most 50 members\n"
        code, out = trace({"ledger/spec.md": spec, "sync/spec.md": SYNC})
        self.assertEqual(code, 1)
        self.assertIn("untested:\n  LEDGER-3.1\n  LEDGER-4.1", out)

    def test_bumped_version_flags_tests_citing_the_old_one(self):
        code, out = trace({"ledger/spec.md": LEDGER.replace("LEDGER-1.1", "LEDGER-1.2"), "sync/spec.md": SYNC})
        self.assertEqual(code, 1)
        self.assertIn("untested:\n  LEDGER-1.2", out)
        self.assertIn("unknown or stale:\n  LEDGER-1.1", out)

    def test_unknown_domain_is_reported(self):
        typo = '<testsuite><testcase name="[LEDER-1.1] typo" /></testsuite>'
        code, out = trace({"ledger/spec.md": LEDGER, "sync/spec.md": SYNC}, extra_reports={"typo.xml": typo})
        self.assertEqual(code, 1)
        self.assertIn("unknown or stale:\n  LEDER-1.1", out)

    def test_number_declared_twice(self):
        spec = LEDGER + "### Requirement: LEDGER-2.2 Remainder goes to the payer\n"
        code, out = trace({"ledger/spec.md": spec, "sync/spec.md": SYNC})
        self.assertEqual(code, 1)
        self.assertIn("duplicate:\n  LEDGER-2: LEDGER-2.1, LEDGER-2.2", out)

    def test_heading_without_valid_id_fails_instead_of_being_skipped(self):
        spec = LEDGER + "### Requirement: Percentage split sums to 100\n"
        code, out = trace({"ledger/spec.md": spec, "sync/spec.md": SYNC})
        self.assertEqual(code, 1)
        self.assertIn("malformed:", out)
        self.assertIn("Percentage split sums to 100", out)

    def test_readme_examples_are_ignored(self):
        code, out = trace({"README.md": "### Requirement: LEDGER-9.1 Example only\n"}, reports=())
        self.assertEqual(code, 0, out)

    def test_empty_project_passes(self):
        code, out = trace({}, reports=())
        self.assertEqual(code, 0, out)

    def test_unreadable_report_fails(self):
        code, out = trace({}, reports=(), extra_reports={"broken.xml": "<testsuite><testcase"})
        self.assertNotEqual(code, 0)
        self.assertIn("cannot read", out)


class StarterConfig(unittest.TestCase):
    def test_required_status_check_is_a_ci_job_name(self):
        ci = (ROOT / "starter/.github/workflows/ci.yml").read_text(encoding="utf-8")
        job_names = set(re.findall(r"^    name: (\S+)$", ci, re.M))
        contexts = set()
        for path in sorted((ROOT / "starter/.github/rulesets").glob("*.json")):
            for rule in json.loads(path.read_text(encoding="utf-8"))["rules"]:
                if rule["type"] == "required_status_checks":
                    contexts |= {c["context"] for c in rule["parameters"]["required_status_checks"]}
        self.assertTrue(contexts)
        self.assertLessEqual(contexts, job_names)


if __name__ == "__main__":
    unittest.main()
