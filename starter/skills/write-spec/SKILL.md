---
name: write-spec
description: Turn an issue's acceptance criteria into spec requirements and failing tests before anyone implements it. Use when starting work on an issue as the spec author.
---

# Write the spec

Format, IDs, EARS sentences, and how tests cite requirements: `docs/specs/README.md`.

## Steps

1. If `gh issue view <N> --json blockedBy` lists an open issue, stop and tell the owner. Otherwise: `gh issue develop <N> --checkout`.
2. Edit every capability the issue touches (`docs/specs/<capability>/spec.md`):
   - New behavior: a new requirement with the next unused number.
   - Changed meaning: bump the version (`LEDGER-2.1` → `LEDGER-2.2`) and update every test that cites it.
   - Removed behavior: delete the requirement and every test that cites it.
   - Bug (the code breaks a requirement that already exists): leave the spec as is, and add a failing test that cites the existing ID and reproduces the bug. If the bug shows the spec itself is wrong, it is changed meaning instead.
   - Name the component ("the API", "the mobile app"), not "the system".
3. Write failing tests that cite the IDs, in the acceptance test paths (`AGENTS.md`). Cover the edge cases where implementers would otherwise invent rules: uneven division, empty, zero, limits, duplicates.
4. Architecture-level choice: write an ADR.
5. Run `bash scripts/check.sh`, then `python3 scripts/trace_check.py`. The new IDs show up as untested until the implementation makes their tests pass; anything else it reports is a mistake to fix now.
6. Commit. Write the PR body into a file from `.github/pull_request_template.md` (`gh` skips the template when given a body): fill `Closes #<N>` and Requirements, and leave the implementer's sections. Then open the draft PR: `gh pr create --draft --title "<title>" --body-file <file> --label enhancement` (or `--label bug`).
7. Ask the owner to review the spec diff in the draft PR, name the commit you are asking about (`git rev-parse HEAD`), and wait. If they want changes, revise the spec and the tests first.
8. Once the owner approves, publish exactly that commit as the approved spec: `git push origin <approved SHA>:refs/heads/spec/<branch>`. Only the owner's account can push `spec/` branches; the implementer starts when this one exists, and review compares the PR against it. Then hand off the branch name. Fetch the exact branches with `git fetch --no-tags origin +refs/heads/main:refs/remotes/origin/main +refs/heads/spec/<branch>:refs/remotes/origin/spec/<branch>`; proceed only if it succeeds. The work order is `git diff refs/remotes/origin/main...refs/remotes/origin/spec/<branch>`, not the issue text.

## Answering the implementer

When the implementer asks about behavior the spec does not cover: decide it with the owner, then add the requirement and a failing test on `spec/<branch>`. Never commit them on the PR branch: it now carries the implementer's commits, and whatever you push to `spec/` counts as approved.

```bash
git fetch --no-tags origin refs/heads/spec/<branch> && git switch --detach FETCH_HEAD
# edit the spec and the acceptance tests, commit
git push origin HEAD:refs/heads/spec/<branch>
```

The implementer takes your commit with `git fetch --no-tags origin refs/heads/spec/<branch> && git merge FETCH_HEAD`.

Independent changes on main are combined automatically during review. If the approved version conflicts with main, check it out as above, run `git fetch --no-tags origin refs/heads/main && git merge FETCH_HEAD`, settle the conflict with the owner, and push. The implementer then merges your update.

## Never

- Put behavior this issue does not build into the specs.
- Implement the task in the same session. The implementer is a separate session.
