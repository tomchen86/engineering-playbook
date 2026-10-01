---
name: review-pr
description: Review a pull request before merge, and merge only the reviewed commit once the owner approves. Use when asked to review or merge a pull request.
---

# Review a pull request

Check the PR out in its own worktree so your other work stays untouched: `git worktree add --detach ../review-<N>`, then run `gh pr checkout <N>` inside it.

## Checklist

1. The PR is marked ready (not a draft), and CI is green: `gh pr checks <N> --watch --fail-fast`.
2. The description has `Closes #<N>` or `No issue: <reason>`, and every template section is filled.
3. Only the listed spec commits touched the tests: `git log --first-parent --no-merges --format=%h <first spec commit>..HEAD -- <test paths>` prints nothing but SHAs listed under `Spec commits:`. Diffing from the latest spec commit alone would miss a test edit made before it.
4. Spec, code, and tests say the same thing, and every test that cites a requirement actually checks it.
5. "Rules discovered during implementation": each must already be in the spec with a test, added by the spec author before it was implemented. Send back any behavior a user or another component would notice that exists only in the code.
6. Traced coverage (its command is in `AGENTS.md`): run only the tests that cite IDs, with coverage on, and list the new branches none of them executes. Each is a missing requirement, dead code, or defensive code. Read function and branch coverage; line coverage cannot see an untaken branch inside a line that ran.
7. Read every change to `AGENTS.md`, `CLAUDE.md`, `skills/`, `.github/`, `scripts/`, test configuration, and dependency files line by line. The first three are the instructions for every later session.
8. Report to the owner: what changed, the risks, and the reviewed head SHA. Cite code with links pinned to that SHA, so they keep pointing at what you reviewed: `gh browse <path>:<line> --commit <sha> --no-browser`.

## Merge

Only when the owner says so:

```bash
gh pr merge <N> --squash --admin --match-head-commit <reviewed SHA>
```

`--admin` is required: only the owner may update main (the `main-merge` ruleset), and `gh` will not use that bypass without it. It is also safe: nobody can bypass `main-integrity`, so `--admin` cannot skip a failing `check`. If the head moved after the review, the merge fails; review the new commits first.

Afterwards, remove the review worktree: `git worktree remove ../review-<N>`.
