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
   - Name the component ("the API", "the mobile app"), not "the system".
3. Write failing tests that cite the IDs. Cover the edge cases where implementers would otherwise invent rules: uneven division, empty, zero, limits, duplicates.
4. Architecture-level choice: write an ADR.
5. Run `bash scripts/check.sh`, then `python3 scripts/trace_check.py`. The new IDs show up as untested until the implementation makes their tests pass; anything else it reports is a mistake to fix now.
6. Commit. Write the PR body into a file from `.github/pull_request_template.md` (`gh` skips the template when given a body): fill `Closes #<N>` and Requirements, including `Spec commits: <sha>`, and leave the implementer's sections. Then open the draft PR: `gh pr create --draft --title "<title>" --body-file <file> --label enhancement` (or `--label bug`).
7. Ask the owner to review the spec diff in the draft PR, and wait. If they want changes, revise the spec and the tests first.
8. Once the owner approves, hand off to the implementer: the branch, the spec diff, and the failing tests. Not the issue text.

## Answering the implementer

When the implementer asks about behavior the spec does not cover: decide it with the owner, add the requirement and a failing test on the same branch, and append this commit to `Spec commits:` in the PR description. Review accepts test changes only from the commits listed there.

## Never

- Put behavior this issue does not build into the specs.
- Implement the task in the same session. The implementer is a separate session.
