#!/usr/bin/env bash
# Is this PR carrying exactly the specs and acceptance tests the owner approved?
# Used by skills/review-pr, step 3.
#
#   usage: bash scripts/spec-check.sh <branch> <acceptance test path>...
#   Run it in a checkout of the PR's head. Paths are literal directories or files,
#   relative to the repo root.
#
# The approved version is the branch spec/<branch>, which only the owner can push
# (.github/rulesets/spec-branches.json). A PR without one has nothing approved, so
# merging it must leave these files exactly as main has them.
#
# Merge main with the approved commit and with the PR head, without touching the
# index or worktree. ok (exit 0) means both merges succeed and their docs/specs and
# acceptance entries match. main supplies attributes; tree entries include modes
# and gitlinks regardless of the PR's diff settings. Requires Git 2.43+.
# A match verifies the merged files, not that the tests make sense or were run.
set -euo pipefail
[ $# -ge 2 ] || { echo "usage: spec-check.sh <branch> <acceptance test path>..." >&2; exit 2; }
branch=$1; shift
paths=(docs/specs "$@")

# One snapshot of origin's branches, matched by exact name and used by commit ID from here
# on. Names are not safe to resolve: the implementer can push a tag called origin/main,
# which git prefers to the remote branch, or a branch whose name merely ends in spec/<branch>.
heads=$(git ls-remote origin 'refs/heads/*')
tip() { awk -v ref="refs/heads/$1" '$2 == ref { print $1 }' <<<"$heads"; }
main=$(tip main); head=$(tip "$branch"); approved=spec/$branch; base=$(tip "$approved")
[ -n "$main" ] && [ -n "$head" ] || { echo "FLAG  origin has no branch main, or no branch $branch"; exit 1; }
if [ -z "$base" ]; then
  echo "note  no $approved on origin: nothing was approved, so merging $branch must leave these files exactly as main has them"
  approved=main; base=$main
fi
git fetch -q --no-tags origin "$main" "$base" "$head"

# What gets compared must be what gets reviewed, and later merged with --match-head-commit.
[ "$(git rev-parse HEAD)" = "$head" ] ||
  { echo "FLAG  the commit checked out here is not the head of $branch: check the PR out again and review that commit"; exit 1; }

# Read literal paths from the repo root, even when called from a subdirectory.
files() { git --literal-pathspecs -c core.quotePath=false ls-tree -r --full-tree "$1" -- "${paths[@]}"; }
differing() { diff <(printf '%s\n' "$1") <(printf '%s\n' "$2") | sed -n $'s/^[<>] [^\t]*\t/      /p' | sort -u; }  # for display
merged() {
  local out
  out=$(git --attr-source="$main" merge-tree --write-tree --name-only --no-messages "$main" "$1") &&
    { printf '%s\n' "$out"; return; }
  echo "FLAG  cannot merge $2 into main; $3 resolves the error or conflict first:" >&2
  tail -n +2 <<<"$out" >&2
  return 1
}

# A path that exists nowhere, such as a mistyped one, would compare nothing and pass.
for path in "$@"; do
  [ -n "$(for commit in "$main" "$base" "$head"; do git --literal-pathspecs ls-tree --full-tree "$commit" -- "$path"; done)" ] ||
    { echo "FLAG  '$path' is on neither main, $approved, nor $branch: use the paths in AGENTS.md on main"; exit 1; }
done
want_tree=$(merged "$base" "$approved" "the spec author")
got_tree=$(merged "$head" "$branch" "the implementer (spec/test conflicts go to the spec author)")
want=$(files "$want_tree"); got=$(files "$got_tree")
compared="$branch $head against $approved $base on main $main"
if [ "$want" = "$got" ]; then
  echo "ok    $compared"
else
  echo "FLAG  $compared: these files are not what was approved"
  differing "$want" "$got" || true
  exit 1
fi
