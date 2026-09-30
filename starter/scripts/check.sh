#!/usr/bin/env bash
# The one command CI and agents run: lint, format check, typecheck, tests.
# Contract: exit non-zero if anything fails, and have the tests write JUnit XML
# into reports/junit/ so scripts/trace_check.py can see which requirements pass.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p reports/junit

# Replace this block with your stack. Examples:
#   Node + vitest: pnpm eslint . && pnpm prettier --check . && pnpm tsc --noEmit &&
#                  pnpm vitest run --reporter=default --reporter=junit --outputFile.junit=reports/junit/vitest.xml
#   Python:        ruff check . && ruff format --check . && mypy . &&
#                  pytest --junitxml=reports/junit/pytest.xml
#   Go:            test -z "$(gofmt -l .)" && go vet ./... &&
#                  go run gotest.tools/gotestsum@latest --junitfile reports/junit/go.xml ./...
echo "scripts/check.sh is not configured yet: pick your stack and replace this block." >&2
exit 1
