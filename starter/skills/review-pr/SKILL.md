---
name: review-pr
description: Review a pull request before merge, and merge only the reviewed commit once the owner approves. Use when asked to review or merge a pull request.
---

# Review a pull request

## Checklist

1. The PR is marked ready (not a draft), and CI is green: `gh pr checks <N>`.
2. The description has `Closes #<N>` or `No issue: <reason>`, and every template section is filled.
3. The tests are unchanged since the spec commit (`Spec commit:` in the PR description): `git diff <spec-commit>..HEAD -- <test paths>` prints nothing.
4. Spec, code, and tests say the same thing, and every test that cites a requirement actually checks it.
5. "Rules discovered during implementation": add each to the spec and a test, or reject it. Never leave one only in the code.
6. For critical areas (playbook chapter 0, level 2): run only the tests that cite IDs, with coverage on, and list the new branches none of them executes. Each is a missing requirement, dead code, or defensive code. Read function and branch coverage; line coverage counts code as run whenever its module loads.
7. Read every change to `.github/`, `scripts/`, test configuration, and dependency files line by line.
8. Report to the owner: what changed, the risks, and the reviewed head SHA.

## Merge

Only when the owner says so:

```bash
gh pr merge <N> --squash --match-head-commit <reviewed SHA>
```

If the head moved after the review, the merge fails. Review the new commits first.
