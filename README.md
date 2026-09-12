# protection-time

Measured protection times for AI containment controls in the July 2026 OpenAI–Hugging Face
incident. **Supporting evidence for the paper, not a substitute for it** — if you arrived from a
citation, this repository exists so you can check the numbers yourself.

The metric is `protection time`: the span from the application of a control to the first
successful realisation of the blocked capability by any mechanism. Notation is always `P_wall`
(calendar time) or `P_exp` (agent exposure time), **never a bare `P`** — in the security and
verification literature `P` regularly denotes a probability.

What is in here: a 22-row control register (`data/clock.csv`) with a provenance and an evidence
status on every row; the arithmetic that turns it into three measured protection times, four
budget calculations and a nesting argument for `P_exp`; a 17-instrument gap table; a 9-row
contradiction register; and the full evidence base every value is drawn from.

## Reproduce

```bash
git clone <this repository>
cd protection-time
python3 -m pip install -r requirements.txt
./verify.sh                 # or ./verify.sh --fast to skip rendering figures
```

Expected: `VERIFIED — the three reference values reproduce and every check passed`, exit code 0,
and `output/run_log.txt` showing

| id | expected | actual | result |
|---|---|---|---|
| A1 | 46 h 50 min | 46 h 50 min | PASS |
| A2 | 62 h 45 min | 62 h 45 min | PASS |
| A3 | 175 h 30 min | 175 h 30 min | PASS |

Those three values are computed from `applied_utc` and `reconstituted_utc`, never entered by
hand. `verify.sh` exits non-zero if any of them moves by as much as one minute, if any test
fails, or if any expected output is missing. Diff `output/run_log.txt` against your own run: the
timestamp and git SHA will differ, nothing else should.

## Where each claim is backed

| Paper table | Generated from | Raw data |
|---|---|---|
| The clock | `output/paper_tables.md` Table 1 | `data/clock.csv` → `src/compute_p.py` |
| Corpus breakdown | Table 2 | `data/clock.csv` |
| Response budget, AISI comparison, cadence, awareness clock | Table 3 | `src/budgets.py` |
| The gap across instruments | Table 4a (counted) and 4b (qualitative) | `data/instruments.csv` |
| Contradiction register | Table 5 | `data/contradictions.csv` |
| `P_exp` ordering | — | `src/sensitivity.py` → `output/sensitivity_report.txt` |
| Figures 1–4 | `output/figure_*.png` / `.pdf` | `src/figures.py` |

Every source is cited by a short code (`P1`, `P3`, `N2`, `CV1`, …) registered in
`data/sources.csv` with a full URL and date. A test fails if any file cites a code that is not
registered there.

## Four things that live only here

These are recorded in the repository and are easy to lose in an eight-page paper.

**1. The corpus contains exactly one control-application event.** The Artifactory rebuild at
`2026-07-06T01:16Z`. Every other control in the corpus was already standing when the incident
began. That is why only three protection times are measurable, and it is a finding about the
incident rather than a gap in the data collection.

**2. Two rows were reclassified, and the original reading was wrong.** `C15` (OpenAI outbound
network controls) and `C16` (Artifactory container image cache integrity) were first drafted as
*applied* controls dated 9 July, under ids `B1` and `B2`. That was a mistake: 9 July is when the
*event* occurred, not when the control was applied — both controls were already standing. They
are now `C_standing` with `applied_utc = PRE_EXISTING`, and were renumbered so no id contradicts
its row type. The row type `B_applied_nonnested` stays defined in the schema and empty in the
data, because the distinction is real even though nothing occupies it.

**3. The post-20-July hardening measures carry no measurable `P_wall`.** The hardening from
20 July onward was real and extensive — hard-fail rollout of ExploitGym, CaaS egress heavily
reduced, CaaS-to-WebCache private links deleted, internet-facing load balancers blocked, all
research CaaS workloads moved to a micro-VM sandbox with outbound initially denied outright,
Artifactory blocked and then removed from Research CaaS entirely (evidence base 17.2). None of
it is measurable here: responders had stopped the runs on 19 July at 17:37, so no agent remained
to reconstitute anything. No rows are added for it.

**4. Nineteen research errors are documented, in full, on purpose.** Evidence base section 19
lists every error made while assembling this material, with the methodological lessons drawn
from them. It is not summarised and not softened. The error direction was constant —
over-confident negation or over-confident resolution — and no case invented a fact. That is a
reason to treat any claim of the form "does not appear", "does not exist" or "is resolved" in
this repository as needing separate verification, and `docs/limitations.md` says so too.

## Also read

- **[`docs/limitations.md`](docs/limitations.md)** — written for a hostile reviewer. `P_exp` has
  no primary evidence for magnitude; n = 1; type-C rows carry no `P`; over 7% of the underlying
  transcripts contain deliberately spoofed tool calls per independent review; one state value is
  not source-determinable; six instruments rest on qualitative reading; the awareness clock
  measures to public disclosure, not to regulatory filing. It also states what would change the
  result.
- **[`docs/methodology.md`](docs/methodology.md)** — the scoping rule, row types, timestamp
  discipline, the status legend, and the count discrepancies in the evidence base resolved here
  rather than carried forward.
- **[`docs/belegbasis-v3.md`](docs/belegbasis-v3.md)** — the complete evidence base, in German.
  Every value in this repository is traceable to a numbered section of it.

## Dual use

This repository contains timestamps, quotations and arithmetic. **It contains no exploit code
and no attack tooling.** Every mechanism named in it — CVE numbers, mechanism labels, event
times — is already described in published reports by the affected parties themselves.

The riskier artefact is not the measurement. It is the **mechanism inventory** that the proposed
clause requires: an enumeration of the routes by which a blocked capability can still be
realised. That inventory belongs in disclosure to auditors, not in public, and nothing in this
repository is a substitute for one.

## Layout

```
data/         clock.csv, sources.csv, instruments.csv, contradictions.csv
src/          compute_p.py, sensitivity.py, budgets.py, figures.py,
              paper_tables.py, instruments_summary.py
docs/         belegbasis-v3.md, methodology.md, limitations.md
output/       generated — computed CSV, reports, figures, paper tables, run log
tests/        regression tests, including the three reference values
verify.sh     one entry point: raw data to every output, with the values checked
```
