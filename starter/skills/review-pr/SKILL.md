---
name: review-pr
description: Review a pull request before merge, and merge only the reviewed commit once the owner approves. Use when asked to review or merge a pull request.
---

# Review a pull request

Check the PR out in its own worktree so your other work stays untouched: `git worktree add --detach ../review-<N>`, then run `gh pr checkout <N>` inside it.

## Checklist

1. The PR is marked ready (not a draft) and up to date with main. If it is behind, run `gh pr update-branch <N>` and refresh this worktree with `gh pr checkout <N>`; send conflicts to the owners described in step 3. Wait for CI on the updated head: `gh pr checks <N> --watch --fail-fast`.
2. The description has `Closes #<N>` or `No issue: <reason>`, and every template section is filled.
3. The specs and acceptance tests are the ones the owner approved. With Git 2.43+, inside the PR's worktree, run main's copy of the check, with the paths from main's `AGENTS.md` (`git show FETCH_HEAD:AGENTS.md` immediately after fetching main). Never take either from the worktree's own files: the PR can edit both.

   ```bash
   f=$(mktemp) && git fetch -q --no-tags origin refs/heads/main && git show FETCH_HEAD:scripts/spec-check.sh > "$f" && bash "$f" <branch> <acceptance test paths>
   ```

   It virtually merges current main with `spec/<branch>` and with the PR head, using main's attributes, then compares their spec and acceptance-test entries. Independent changes on main merge automatically; a PR without a spec branch must leave the merged files as main has them. It passes only when it exits successfully and prints an `ok` line; keep that line, including main's SHA, for your report. Differences or conflicts in specs/tests go to the spec author; code conflicts go to the implementer. A match verifies the merged files, not that the tests make sense or ran: that is step 4 and CI.
4. Spec, code, and tests say the same thing, and every test that cites a requirement actually checks it. No test outside the acceptance test paths cites an ID: the implementer's own tests are not evidence for a requirement.
5. "Rules discovered during implementation": each must already be in the spec with a test, added by the spec author before it was implemented. Send back any behavior a user or another component would notice that exists only in the code.
6. Traced coverage (its command is in `AGENTS.md`): run only the tests that cite IDs, with coverage on, and list the new branches none of them executes. Each is a missing requirement, dead code, or defensive code. Read function and branch coverage; line coverage cannot see an untaken branch inside a line that ran.
7. Read every change to `AGENTS.md`, `CLAUDE.md`, `skills/`, `.github/`, `scripts/`, test configuration, and dependency files line by line. The first three are the instructions for every later session.
8. Report to the owner: what changed, the risks, the reviewed head SHA, and the spec SHA step 3 compared it with. Cite code with links pinned to that SHA, so they keep pointing at what you reviewed: `gh browse <path>:<line> --commit <sha> --no-browser`.

## Merge

Only when the owner says so. If the PR has fallen behind main, update it as in step 1, review the new commits, and update your report before proceeding. Run step 3 again against current main: the PR head and approved spec SHAs must still match your report, or review their new commits first. Then:

```bash
gh pr merge <N> --squash --admin --match-head-commit <reviewed SHA>
```

`--admin` is required: only the owner may update main (the `main-merge` ruleset), and `gh` will not use that bypass without it. It is also safe: nobody can bypass `main-integrity`, so `--admin` cannot skip a failing `check` or merge a branch behind main. If the head moved after the review, the merge fails; review the new commits first.

Afterwards, delete the spec branch if there was one (`git push origin --delete refs/heads/spec/<branch>`), and remove the review worktree: `git worktree remove ../review-<N>`.
