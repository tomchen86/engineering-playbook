#!/usr/bin/env bash
# The one command CI and agents run: lint, format check, typecheck, tests, then the
# requirement trace. Contract for the block below: exit non-zero if anything fails, and
# have the tests write JUnit XML into reports/junit/ so scripts/trace_check.py can see
# which requirements pass.
set -euo pipefail
cd "$(dirname "$0")/.."
# Start empty: a stale report would let a removed or now-skipped test still count.
rm -rf reports/junit && mkdir -p reports/junit
# The trace runs last, even when a step below fails: in the red phase its report is the
# point. Keep this line when you replace the block.
trap 'status=$?; python3 scripts/trace_check.py || status=1; exit "$status"' EXIT

# Replace this block with your stack. Examples:
#   Node + vitest: pnpm eslint . && pnpm prettier --check . && pnpm tsc --noEmit &&
#                  pnpm vitest run --reporter=default --reporter=junit --outputFile.junit=reports/junit/vitest.xml
#   Python:        ruff check . && ruff format --check . && mypy . &&
#                  pytest --junitxml=reports/junit/pytest.xml
#   Go:            test -z "$(gofmt -l .)" && go vet ./... &&
#                  go run gotest.tools/gotestsum@latest --junitfile reports/junit/go.xml ./...
echo "scripts/check.sh is not configured yet: pick your stack and replace this block." >&2
exit 1
