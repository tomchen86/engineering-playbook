#!/usr/bin/env bash
# One-time GitHub setup for a new repo: merge settings, labels, rulesets.
# Safe to re-run. Run from a clone after the first push, logged in to gh as the owner.
set -euo pipefail
cd "$(dirname "$0")/.."

# Squash merges only, and delete the branch once its PR merges.
gh repo edit --enable-squash-merge --enable-merge-commit=false --enable-rebase-merge=false --delete-branch-on-merge

# Labels that sort release notes (.github/release.yml). --force updates existing ones.
gh label create enhancement --color a2eeef --description "New feature or request" --force
gh label create bug --color d73a4a --description "Something isn't working" --force
gh label create skip-changelog --color ededed --description "Leave out of release notes" --force

# Rulesets from .github/rulesets/, skipping the ones that already exist.
existing=$(gh api "repos/{owner}/{repo}/rulesets" --jq '.[].name')
for f in .github/rulesets/*.json; do
  name=$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["name"])' "$f")
  if grep -qxF "$name" <<<"$existing"; then echo "ruleset already exists: $name"; continue; fi
  gh api -X POST "repos/{owner}/{repo}/rulesets" --input "$f" >/dev/null
  echo "ruleset created: $name"
done

# Secret scanning blocks pushes that contain keys. Free on public repos; report its state.
gh api "repos/{owner}/{repo}" --jq '"secret scanning: \(.security_and_analysis.secret_scanning.status // "unavailable"), push protection: \(.security_and_analysis.secret_scanning_push_protection.status // "unavailable")"'
