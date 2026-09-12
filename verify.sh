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

bold "Protection time - full verification"
printf '%s\n' "python: $("$PYTHON" --version 2>&1)"

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
  else
    fail "$id  P_wall = '$actual', expected '${REFERENCE[$id]}'"
  fi
done

step "Checking that no type-C row carries a P_wall"
"$PYTHON" - <<'PY'
import csv, sys
from pathlib import Path
with Path("output/clock_computed.csv").open(newline="", encoding="utf-8") as handle:
    offenders = [r["id"] for r in csv.DictReader(handle)
                 if r["row_type"] == "C_standing" and (r["p_wall_hours"] or r["p_wall_hhmm"])]
if offenders:
    print(f"    type C rows carrying a P_wall: {offenders}", file=sys.stderr)
    sys.exit(1)
PY
ok "0 of 16 type-C rows carry a P_wall"

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

step "Generating the paper tables"
"$PYTHON" src/paper_tables.py --quiet
ok "output/paper_tables.md"

# --- 2. the test suite ------------------------------------------------------
step "Running the test suite"
if "$PYTHON" -m pytest tests/ -q; then
  ok "all tests passed"
else
  fail "test suite"
fi

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
for path in "${EXPECTED[@]}"; do
  if [[ -s "$path" ]]; then
    ok "$path"
  else
    fail "$path is missing or empty"
  fi
done

# --- verdict ----------------------------------------------------------------
printf '\n'
if [[ $FAILURES -eq 0 ]]; then
  bold "VERIFIED - the three reference values reproduce and every check passed."
  exit 0
fi
bold "FAILED - $FAILURES check(s) did not pass."
exit 1
