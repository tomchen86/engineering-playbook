"""Self-test for starter/scripts/spec-check.sh, on a local git fixture (no GitHub involved).

The spec author writes spec + acceptance tests on codex/feat and, once the owner approves,
pushes that commit to spec/codex/feat. The implementer then pushes to codex/feat. The script
runs in a separate single-branch clone, as a reviewer's checkout may be.
"""
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "starter" / "scripts" / "spec-check.sh"
SPEC = "docs/specs/ledger/spec.md"
TEST = "tests/acceptance/ledger.test"
R1, R2, R3 = (f"### Requirement: LEDGER-{n}.1\n" for n in (1, 2, 3))
SYNC = {"docs/specs/sync/spec.md": "### Requirement: SYNC-1.1\n", "tests/acceptance/sync.test": "case 1\n"}
APPROVED = "refs/remotes/origin/spec/codex/feat"


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class SpecCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        origin = str(self.tmp / "origin.git")
        git(self.tmp, "init", "-q", "--bare", "-b", "main", origin)
        self.repo = self.tmp / "work"
        git(self.tmp, "init", "-q", "-b", "main", "work")
        git(self.repo, "remote", "add", "origin", origin)
        git(self.repo, "config", "user.email", "t@t")
        git(self.repo, "config", "user.name", "t")
        self.commit("base", {SPEC: R1, TEST: "case 1\n"})
        git(self.repo, "push", "-q", "origin", "main")
        git(self.tmp, "clone", "-q", "--single-branch", "--branch", "main", origin, "review")
        git(self.repo, "switch", "-q", "-c", "codex/feat")
        self.spec = self.commit("spec author", {SPEC: R1 + R2, TEST: "case 1\ncase 2\n"})
        git(self.repo, "push", "-q", "origin", f"{self.spec}:refs/heads/spec/codex/feat")
        self.commit("implementation", {"src/impl": "code\n", "tests/unit/impl.test": "case helper\n"})

    def commit(self, message, files):
        for rel, text in files.items():
            path = self.repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", message)
        return git(self.repo, "rev-parse", "HEAD")

    def on_main(self, files):
        """Someone else's PR merges into main while this one is open."""
        git(self.repo, "switch", "-q", "main")
        self.commit("someone else's PR", files)
        git(self.repo, "push", "-q", "origin", "main")
        git(self.repo, "switch", "-q", "codex/feat")

    def spec_author(self, files=None, merge_main=False, remove=None):
        """The spec author, pushing as the owner, updates spec/codex/feat."""
        git(self.repo, "switch", "-q", "--detach", APPROVED)
        if merge_main:
            git(self.repo, "merge", "-q", "--no-edit", "main")
        if remove:
            git(self.repo, "rm", "-q", remove)
            git(self.repo, "commit", "-q", "-m", "spec author removes a test")
        if files:
            self.commit("spec author", files)
        git(self.repo, "push", "-q", "origin", "HEAD:refs/heads/spec/codex/feat")
        git(self.repo, "switch", "-q", "codex/feat")

    def check(self, branch="codex/feat", path="tests/acceptance", checkout=True):
        """Push the branch, check its head out in the reviewer's clone, and run the script there."""
        git(self.repo, "push", "-q", "-f", "origin", branch)
        review = self.tmp / "review"
        if checkout:
            git(review, "fetch", "-q", "origin", f"+refs/heads/{branch}:refs/remotes/origin/{branch}")
            git(review, "checkout", "-q", "--detach", f"refs/remotes/origin/{branch}")
        # Run from a subdirectory: the paths must still be read from the repo root.
        result = subprocess.run(["bash", str(SCRIPT), branch, path],
                                cwd=review / "docs", capture_output=True, text=True)
        return result.returncode, result.stdout + result.stderr

    def test_untouched_specs_and_acceptance_tests_pass_and_both_shas_are_reported(self):
        head = git(self.repo, "rev-parse", "HEAD")
        code, out = self.check()
        self.assertEqual(code, 0, out)
        self.assertIn(f"ok    codex/feat {head} against spec/codex/feat {self.spec}", out)

    def test_any_change_is_flagged_even_a_pure_addition(self):
        for files in ({TEST: "case 1\ncase 2\nreturn\n"},
                      {"tests/acceptance/conftest.py": "mock the code under test\n"},
                      {SPEC: R1 + "### Requirement: LEDGER-2.1 roughly\n"}):
            with self.subTest(files=files):
                self.commit("implementer", files)
                code, out = self.check()
                self.assertEqual(code, 1, out)
                self.assertIn("these files are not what was approved\n      " + next(iter(files)), out)
                git(self.repo, "reset", "-q", "--hard", "HEAD~1")

    def test_a_gitlink_is_compared_even_when_the_pr_tells_git_to_ignore_it(self):
        (self.repo / ".gitmodules").write_text(
            '[submodule "x"]\n\tpath = tests/acceptance/vendored\n\turl = ./x.git\n\tignore = all\n')
        git(self.repo, "add", ".gitmodules")
        git(self.repo, "update-index", "--add", "--cacheinfo", f"160000,{self.spec},tests/acceptance/vendored")
        git(self.repo, "commit", "-q", "-m", "implementer")
        self.assertEqual(git(self.repo, "diff", "--name-only", self.spec, "HEAD", "--", "tests/acceptance"), "")
        code, out = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("tests/acceptance/vendored", out)

    def test_a_changed_approved_gitlink_is_compared_despite_ignore_all(self):
        replacement = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "switch", "-q", "--detach", APPROVED)
        git(self.repo, "update-index", "--add", "--cacheinfo", f"160000,{self.spec},tests/acceptance/vendored")
        git(self.repo, "commit", "-qm", "spec author adds a gitlink")
        git(self.repo, "push", "-q", "origin", "HEAD:refs/heads/spec/codex/feat")
        git(self.repo, "switch", "-q", "codex/feat")
        git(self.repo, "merge", "-q", "--no-edit", APPROVED)
        (self.repo / ".gitmodules").write_text(
            '[submodule "x"]\n\tpath = tests/acceptance/vendored\n\turl = ./x.git\n\tignore = all\n')
        git(self.repo, "add", ".gitmodules")
        git(self.repo, "update-index", "--cacheinfo", f"160000,{replacement},tests/acceptance/vendored")
        git(self.repo, "commit", "-qm", "implementer changes the gitlink")
        self.assertEqual(git(self.repo, "diff", "--name-only", APPROVED, "HEAD", "--", "tests/acceptance"), "")
        code, out = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("tests/acceptance/vendored", out)

    def test_unrelated_specs_on_main_need_no_spec_branch_refresh(self):
        self.on_main(SYNC)
        for sync in (False, True):
            with self.subTest(pr_has_main=sync):
                if sync:
                    git(self.repo, "merge", "-q", "--no-edit", "main")
                code, out = self.check()
                self.assertEqual(code, 0, out)
                self.assertIn("ok    ", out)

    def test_dropping_what_main_added_is_flagged(self):
        """The PR's own copies still equal the stale spec/<branch>, so comparing only those two would pass."""
        self.on_main(SYNC)
        git(self.repo, "merge", "-q", "--no-edit", "main")
        git(self.repo, "rm", "-q", *SYNC)
        git(self.repo, "commit", "-q", "-m", "tidy")
        self.assertEqual(git(self.repo, "diff", "--name-only", self.spec, "HEAD", "--", "docs/specs", "tests/acceptance"), "")
        code, out = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("these files are not what was approved\n      docs/specs/sync/spec.md", out)

    def test_a_code_conflict_goes_to_the_implementer(self):
        self.on_main({"src/impl": "someone else's code\n"})
        code, out = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("the implementer", out)
        self.assertIn("src/impl", out)

    def test_a_spec_conflict_goes_to_the_spec_author(self):
        self.on_main({TEST: "main rewrites the test\n"})
        code, out = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("the spec author", out)
        self.assertIn(TEST, out)

    def test_pr_attributes_cannot_resolve_the_approved_versions_conflict(self):
        self.on_main({TEST: "main rewrites the test\n"})
        self.commit("implementer sets union", {".gitattributes": "tests/acceptance/** merge=union\n"})
        # In the PR's context Git would silently combine the conflicting versions.
        tree = git(self.repo, "merge-tree", "--write-tree", "main", APPROVED)
        combined = git(self.repo, "show", f"{tree}:{TEST}") + "\n"
        git(self.repo, "merge", "-q", "--no-edit", "main")
        self.commit("implementer chooses the combined test", {TEST: combined})
        code, out = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("the spec author", out)

    def test_equal_snapshots_do_not_hide_a_different_squash_result(self):
        original = "policy=old\nkeep1\nkeep2\nkeep3\nkeep4\nverify=old\n"
        approved = original.replace("verify=old", "verify=new")
        self.on_main({TEST: original})
        self.spec_author(files={TEST: original})
        self.spec_author(merge_main=True, files={TEST: approved})
        git(self.repo, "merge", "-q", "--no-edit", APPROVED)
        self.on_main({TEST: original.replace("policy=old", "policy=new")})
        self.spec_author(merge_main=True, files={TEST: approved})
        self.assertEqual(git(self.repo, "diff", "--name-only", APPROVED, "HEAD", "--", TEST), "")
        code, out = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn(TEST, out)
        git(self.repo, "merge", "-q", "--no-edit", APPROVED)
        self.assertEqual(self.check()[0], 0)

    def test_virtual_results_agree_with_local_squash_merges(self):
        self.on_main(SYNC)
        self.assertEqual(self.check()[0], 0)
        main = git(self.repo, "rev-parse", "main")
        for ref in (APPROVED, "codex/feat"):
            with self.subTest(ref=ref):
                expected = git(self.repo, f"--attr-source={main}", "merge-tree", "--write-tree", main, ref)
                git(self.repo, "switch", "-q", "--detach", main)
                git(self.repo, "merge", "-q", "--squash", ref)
                self.assertEqual(git(self.repo, "write-tree"), expected)
                git(self.repo, "reset", "-q", "--hard", main)

    def test_a_spec_update_must_be_merged_into_the_pr(self):
        self.spec_author({SPEC: R1 + R2 + R3, TEST: "case 1\ncase 2\ncase 3\n"})
        code, out = self.check()
        self.assertEqual(code, 1, out)
        git(self.repo, "merge", "-q", "--no-edit", APPROVED)
        code, out = self.check()
        self.assertEqual(code, 0, out)

    def test_an_approved_removal_of_the_last_acceptance_test_passes(self):
        self.spec_author(remove=TEST)
        git(self.repo, "merge", "-q", "--no-edit", APPROVED)
        code, out = self.check()
        self.assertEqual(code, 0, out)

    def test_an_empty_acceptance_directory_can_stay_tracked(self):
        self.spec_author(remove=TEST, files={SPEC: "", "tests/acceptance/.gitkeep": ""})
        git(self.repo, "merge", "-q", "--no-edit", APPROVED)
        self.assertEqual(self.check()[0], 0)
        git(self.repo, "switch", "-q", "main")
        git(self.repo, "merge", "-q", "--squash", "codex/feat")
        git(self.repo, "commit", "-qm", "remove the last requirement and test")
        git(self.repo, "push", "-q", "origin", "main")
        git(self.repo, "switch", "-q", "-c", "refactor")
        self.commit("refactor", {"src/impl": "tidier\n"})
        self.assertEqual(self.check("refactor")[0], 0)

    def run_review_command(self, review):
        skill = SCRIPT.parents[1] / "skills/review-pr/SKILL.md"
        command = re.search(r"```bash\n(.*?)\n\s*```", skill.read_text(), re.S).group(1)
        command = command.replace("<branch>", "codex/feat").replace("<acceptance test paths>", "tests/acceptance")
        return subprocess.run(["bash", "-c", command], cwd=review, capture_output=True, text=True)

    def test_documented_loader_fails_when_main_has_no_script(self):
        result = self.run_review_command(self.tmp / "review")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("ok    ", result.stdout)

    def test_documented_loader_fetches_main_in_a_pr_only_clone_with_a_shadow_tag(self):
        self.on_main({"scripts/spec-check.sh": 'echo "TRUSTED_MAIN"\n'})
        self.commit("fake main script", {"scripts/spec-check.sh": 'echo "UNTRUSTED_TAG"\n'})
        git(self.repo, "tag", "refs/remotes/origin/main")
        git(self.repo, "push", "-q", "origin", "codex/feat", "refs/tags/refs/remotes/origin/main")
        git(self.tmp, "clone", "-q", "--single-branch", "--branch", "codex/feat", str(self.tmp / "origin.git"), "pr-only")
        result = self.run_review_command(self.tmp / "pr-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "TRUSTED_MAIN\n")

    def test_documented_work_order_ignores_shadow_tags(self):
        self.commit("unapproved spec", {SPEC: "UNAPPROVED\n"})
        for name in ("origin/main", "origin/spec/codex/feat"):
            git(self.repo, "tag", name)
            git(self.repo, "push", "-q", "origin", f"refs/tags/{name}")
        review = self.tmp / "review"
        git(review, "fetch", "-q", "--tags", "origin", "+refs/heads/spec/codex/feat:refs/remotes/origin/spec/codex/feat")
        for name in ("skills/write-spec/SKILL.md", "AGENTS.md"):
            with self.subTest(document=name):
                source = (SCRIPT.parents[1] / name).read_text()
                command = re.search(r"[Ww]ork order is `([^`]+)`", source).group(1).replace("<branch>", "codex/feat")
                result = subprocess.run(["bash", "-c", command], cwd=review, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(R2.strip(), result.stdout)
                self.assertNotIn("UNAPPROVED", result.stdout)

    def test_a_head_that_moved_after_checkout_is_flagged(self):
        self.assertEqual(self.check()[0], 0)
        self.commit("implementer pushes again", {"src/impl": "more code\n"})
        code, out = self.check(checkout=False)
        self.assertEqual(code, 1, out)
        self.assertIn("FLAG  the commit checked out here is not the head of codex/feat", out)

    def test_tags_named_like_remote_branches_do_not_stand_in_for_them(self):
        """Where tags are unprotected the implementer can push them, and git resolves origin/x to a tag first."""
        tampered = self.commit("implementer", {TEST: "case 1\ncase 2\nreturn\n"})
        for name in ("origin/main", "origin/spec/codex/feat"):
            git(self.repo, "tag", name, tampered)
            git(self.repo, "push", "-q", "origin", f"refs/tags/{name}")
        git(self.repo, "push", "-q", "-f", "origin", "codex/feat")
        git(self.tmp / "review", "fetch", "-q", "--tags", "origin")
        code, out = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn(TEST, out)

    def test_a_branch_whose_name_only_ends_like_the_spec_branch_is_not_the_spec(self):
        git(self.repo, "switch", "-q", "-c", "refactor", "main")
        tampered = self.commit("implementer", {TEST: "case 1 skipped\n"})
        git(self.repo, "push", "-q", "origin", f"{tampered}:refs/heads/refs/heads/spec/refactor")
        code, out = self.check("refactor")
        self.assertEqual(code, 1, out)
        self.assertIn("note  no spec/refactor", out)
        self.assertIn(TEST, out)

    def test_a_mistyped_path_is_flagged_instead_of_comparing_nothing(self):
        self.commit("implementer", {TEST: "case 1\ncase 2\nreturn\n"})
        code, out = self.check(path="tests/acceptence")
        self.assertEqual(code, 1, out)
        self.assertIn("FLAG  'tests/acceptence' is on neither main, spec/codex/feat, nor codex/feat", out)

    def test_a_path_cannot_carry_pathspec_magic_that_excludes_the_specs(self):
        self.commit("implementer", {SPEC: "another spec\n"})
        code, out = self.check(path=":(exclude)docs/specs")
        self.assertNotEqual(code, 0, out)
        self.assertNotIn("ok    ", out)

    def test_without_a_spec_branch_nothing_may_change(self):
        git(self.repo, "switch", "-q", "-c", "refactor", "main")
        self.commit("refactor", {"src/impl": "tidier\n"})
        code, out = self.check("refactor")
        self.assertEqual(code, 0, out)
        self.assertIn("note  no spec/refactor", out)
        self.commit("and a test tweak", {TEST: "case 1 skipped\n"})
        code, out = self.check("refactor")
        self.assertEqual(code, 1, out)
        self.assertIn(TEST, out)


if __name__ == "__main__":
    unittest.main()
