#!/usr/bin/env bash
#
# One entry point: raw data -> every output, with the reference values checked.
#
#   ./verify.sh              full pipeline
#   ./verify.sh --fast       skip the figures (no matplotlib render)
#
# Exits non-zero if any reference value fails to reproduce, if any test fails,
# or if any expected output is missing. A reviewer should be able to clone the
# repository, install the requirements, and run this.

set -euo pipefail

cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
FAST=0
[[ "${1:-}" == "--fast" ]] && FAST=1

# The three reference values from evidence base 4.3. If these move, the
# arithmetic or the data is wrong and nothing downstream can be trusted.
declare -A REFERENCE=(
  [A1]="46 h 50 min"
  [A2]="62 h 45 min"
  [A3]="175 h 30 min"
)

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
step() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }
ok()   { printf '    \033[32mok\033[0m   %s\n' "$1"; }
fail() { printf '    \033[31mFAIL\033[0m %s\n' "$1" >&2; FAILURES=$((FAILURES + 1)); }

FAILURES=0

RUN_LOG="output/run_log.txt"
mkdir -p output
: > "$RUN_LOG"

# Everything a reviewer needs to diff their run against this one.
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
GIT_SHA="$(git rev-parse HEAD 2>/dev/null || echo "not a git checkout")"
GIT_DIRTY="$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
PYTHON_VERSION="$("$PYTHON" --version 2>&1)"

log() { printf '%s\n' "$1" >> "$RUN_LOG"; }

log "protection-time verification run log"
log "===================================="
log ""
log "timestamp (UTC)   $TIMESTAMP"
log "git SHA           $GIT_SHA"
log "working tree      $([[ "$GIT_DIRTY" == "0" ]] && echo "clean" || echo "$GIT_DIRTY uncommitted file(s)")"
log "python            $PYTHON_VERSION"
log "platform          $(uname -srm)"
log "mode              $([[ $FAST -eq 1 ]] && echo "--fast (figures skipped)" || echo "full")"
for module in numpy matplotlib pytest; do
  version="$("$PYTHON" -c "import $module; print($module.__version__)" 2>/dev/null || echo "not installed")"
  log "$(printf '%-17s %s' "$module" "$version")"
done
log ""
log "Reference values - evidence base 4.3. These are computed from applied_utc and"
log "reconstituted_utc in data/clock.csv, never entered by hand."
log ""
log "$(printf '%-4s %-14s %-14s %s' "id" "expected" "actual" "result")"
log "$(printf '%-4s %-14s %-14s %s' "----" "--------------" "--------------" "------")"

bold "Protection time - full verification"
printf '%s\n' "python: $PYTHON_VERSION"
printf '%s\n' "git:    $GIT_SHA"

# --- 0. dependencies --------------------------------------------------------
step "Checking dependencies"
MISSING=()
for module in numpy pytest; do
  "$PYTHON" -c "import $module" 2>/dev/null || MISSING+=("$module")
done
if [[ $FAST -eq 0 ]]; then
  "$PYTHON" -c "import matplotlib" 2>/dev/null || MISSING+=("matplotlib")
fi
if [[ ${#MISSING[@]} -gt 0 ]]; then
  printf '    missing: %s\n' "${MISSING[*]}" >&2
  printf '    install with: %s -m pip install -r requirements.txt\n' "$PYTHON" >&2
  exit 1
fi
ok "numpy, pytest$([[ $FAST -eq 0 ]] && echo ', matplotlib')"

# --- 1. the pipeline --------------------------------------------------------
step "Computing P_wall from data/clock.csv"
"$PYTHON" src/compute_p.py --quiet
ok "output/clock_computed.csv"

step "Checking the reference values against evidence base 4.3"
for id in A1 A2 A3; do
  actual="$("$PYTHON" - "$id" <<'PY'
import csv, sys
from pathlib import Path
target = sys.argv[1]
with Path("output/clock_computed.csv").open(newline="", encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        if row["id"] == target:
            print(row["p_wall_hhmm"])
            break
    else:
        print("MISSING")
PY
)"
  if [[ "$actual" == "${REFERENCE[$id]}" ]]; then
    ok "$id  P_wall = $actual"
    log "$(printf '%-4s %-14s %-14s %s' "$id" "${REFERENCE[$id]}" "$actual" "PASS")"
  else
    fail "$id  P_wall = '$actual', expected '${REFERENCE[$id]}'"
    log "$(printf '%-4s %-14s %-14s %s' "$id" "${REFERENCE[$id]}" "$actual" "FAIL")"
  fi
done

step "Checking that no type-C row carries a P_wall"
if "$PYTHON" - <<'PY'
import csv, sys
from pathlib import Path
with Path("output/clock_computed.csv").open(newline="", encoding="utf-8") as handle:
    offenders = [r["id"] for r in csv.DictReader(handle)
                 if r["row_type"] == "C_standing" and (r["p_wall_hours"] or r["p_wall_hhmm"])]
if offenders:
    print(f"    type C rows carrying a P_wall: {offenders}", file=sys.stderr)
    sys.exit(1)
PY
then
  ok "no type-C row carries a P_wall"
  TYPE_C_STATUS=PASS
else
  fail "a type-C row carries a P_wall"
  TYPE_C_STATUS=FAIL
fi

step "Running the nesting argument and the Monte Carlo demonstration"
"$PYTHON" src/sensitivity.py --quiet
ok "output/sensitivity_report.txt"

step "Running the budget, cadence and awareness arithmetic"
"$PYTHON" src/budgets.py --quiet
ok "output/budgets_report.txt"

if [[ $FAST -eq 0 ]]; then
  step "Rendering figures"
  "$PYTHON" src/figures.py --quiet
  ok "4 figures, PNG and PDF"
else
  step "Rendering figures"
  printf '    skipped (--fast)\n'
fi

step "Refreshing the generated instruments summary"
"$PYTHON" src/instruments_summary.py --quiet
ok "data/instruments.csv summary row"

step "Generating the paper tables"
"$PYTHON" src/paper_tables.py --quiet
ok "output/paper_tables.md"

# --- 2. the test suite ------------------------------------------------------
step "Running the test suite"
TEST_OUTPUT="$("$PYTHON" -m pytest tests/ -q 2>&1)" && TEST_STATUS=0 || TEST_STATUS=1
printf '%s\n' "$TEST_OUTPUT"
# Strip the elapsed time: the log is meant to be diffable, so nothing in it
# may vary between two runs of the same commit.
TEST_SUMMARY="$(printf '%s\n' "$TEST_OUTPUT" | tail -n 1 | sed -E 's/ in [0-9]+\.[0-9]+s$//')"
if [[ $TEST_STATUS -eq 0 ]]; then
  ok "all tests passed"
else
  fail "test suite"
fi
log ""
log "Other invariants"
log "----------------"
log "$(printf '%-52s %s' "test suite ($TEST_SUMMARY)" "$([[ $TEST_STATUS -eq 0 ]] && echo PASS || echo FAIL)")"

# --- 3. expected outputs ----------------------------------------------------
step "Checking that every expected output exists"
EXPECTED=(
  output/clock_computed.csv
  output/sensitivity_report.txt
  output/budgets_report.txt
  output/paper_tables.md
)
if [[ $FAST -eq 0 ]]; then
  for stem in figure_1_timeline figure_2_cadence figure_3_states figure_4_awareness_clock; do
    EXPECTED+=("output/$stem.png" "output/$stem.pdf")
  done
fi
MISSING_OUTPUTS=0
for path in "${EXPECTED[@]}"; do
  if [[ -s "$path" ]]; then
    ok "$path"
  else
    fail "$path is missing or empty"
    MISSING_OUTPUTS=$((MISSING_OUTPUTS + 1))
  fi
done
log "$(printf '%-52s %s' "no type-C row carries a P_wall" "$TYPE_C_STATUS")"
log "$(printf '%-52s %s' "expected outputs present (${#EXPECTED[@]})" "$([[ $MISSING_OUTPUTS -eq 0 ]] && echo PASS || echo FAIL)")"
log "$(printf '%-52s %s' "instruments with a containment time axis" "$("$PYTHON" -c "
import csv
rows = list(csv.DictReader(open('data/instruments.csv', encoding='utf-8')))
print(sum(1 for r in rows if r['n_time_axis_present'] != 'FALSE'), '(expected 0)')
")")"

# --- verdict ----------------------------------------------------------------
log ""
if [[ $FAILURES -eq 0 ]]; then
  log "VERDICT  VERIFIED - all reference values reproduce and every check passed."
else
  log "VERDICT  FAILED - $FAILURES check(s) did not pass."
fi
log ""
log "Diff this file against your own run. The timestamp and git SHA will differ;"
log "nothing else should."

printf '\n'
printf '    wrote %s\n' "$RUN_LOG"
printf '\n'
if [[ $FAILURES -eq 0 ]]; then
  bold "VERIFIED - the three reference values reproduce and every check passed."
  exit 0
fi
bold "FAILED - $FAILURES check(s) did not pass."
exit 1
