# Paper claims check

**Generated file — do not edit by hand.** Regenerate with `python3 src/check_claims.py`.

Every quantitative claim in `output/paper.md` is listed with the file it should trace to and the value the repository yields when that file is recomputed. Claims that do not reproduce are reported here, not reconciled: where the prose and the data disagree, the disagreement is the finding.

**52 of 55 claims reproduce.** 2 do not. 1 cannot be resolved to a file.

## Claims requiring attention

### DOES NOT REPRODUCE — §3: Twenty-five primary sources

- **Source:** `data/sources.csv`
- **Paper says:** 25
- **Repository yields:** 23 P-coded; 26 read in full or in part; 38 primary rows in total
- **Note:** No reading of the register yields 25. Nearest is 23 P-coded entries, and the register has grown by P24 and P25 since the text was drafted. Reported, not reconciled.

### DOES NOT REPRODUCE — §3: nine standards or frameworks

- **Source:** `data/sources.csv`
- **Paper says:** 9
- **Repository yields:** 11
- **Note:** The register now holds eleven framework rows: N1-N9 plus N10 (MITRE ATT&CK) and N11 (METR Frontier Risk Report), both added after the text was drafted. Reported, not reconciled.

### not resolvable to a file — §1: published three weeks after the last public timeline reconstruction

- **Source:** `data/sources.csv`
- **Paper says:** three weeks
- **Repository yields:** not computable
- **Note:** The register does not identify which artefact 'the last public timeline reconstruction' denotes. Candidates and their gaps to 26 August: Black Hat transcript 5 August (21 days, exactly three weeks), CrowdStrike 4 August (22), SecureLayer7 30 July (27), Hugging Face timeline 27 July (30). Reported, not reconciled.

---

## All claims

| § | Claim | Source | Paper | Repository | Result |
|---|---|---|---|---|---|
| Abstract, 4.1 | A1 protection time 46 h 50 min | `data/clock.csv -> output/clock_computed.csv` | 46 h 50 min | 46 h 50 min | ok |
| Abstract, 4.1 | A2 protection time 62 h 45 min | `data/clock.csv -> output/clock_computed.csv` | 62 h 45 min | 62 h 45 min | ok |
| Abstract, 4.1 | A3 protection time 175 h 30 min | `data/clock.csv -> output/clock_computed.csv` | 175 h 30 min | 175 h 30 min | ok |
| Abstract, 3, 4.1 | single control application at 2026-07-06 01:16 UTC | `data/clock.csv -> output/clock_computed.csv` | 2026-07-06T01:16Z | 2026-07-06T01:16Z | ok |
| 4.1 | realisation 2026-07-08 00:06 UTC (egress) | `data/clock.csv -> output/clock_computed.csv` | 2026-07-08T00:06Z | 2026-07-08T00:06Z | ok |
| 4.1 | realisation 2026-07-08 16:01 UTC (inter-agent) | `data/clock.csv -> output/clock_computed.csv` | 2026-07-08T16:01Z | 2026-07-08T16:01Z | ok |
| 4.1 | realisation 2026-07-13 08:46 UTC (admin) | `data/clock.csv -> output/clock_computed.csv` | 2026-07-13T08:46Z | 2026-07-13T08:46Z | ok |
| 4.1 | control held: HTTP 400 at 2026-07-06 12:56 UTC | `data/clock.csv -> output/clock_computed.csv` | 2026-07-06T12:56Z | 2026-07-06T12:56Z | ok |
| 4.2, Abstract | all three controls bypassed, none broken | `data/clock.csv -> output/clock_computed.csv` | bypassed x3 | bypassed x3 | ok |
| 5 | rounded to 47, 63 and 176 hours | `data/clock.csv -> output/clock_computed.csv` | 47/63/176 | 47/63/176 | ok |
| 3 | sixteen of the twenty-two rows are standing controls | `data/clock.csv -> output/clock_computed.csv` | 16 of 22 | 16 of 22 | ok |
| 3 | exactly one control-application event | `data/clock.csv -> output/clock_computed.csv` | 1 | 1 | ok |
| 4.3 | three out-of-corpus rows, three separate incidents | `data/clock.csv -> output/clock_computed.csv` | 3 | 3 | ok |
| 5 | one row's state not determinable from the source | `data/clock.csv -> output/clock_computed.csv` | 1 | 1 | ok |
| 5 | five egress controls at Hugging Face | `data/clock.csv -> output/clock_computed.csv` | 5 | 5 | ok |
| Abstract, 1, 4.7, 6 | seventeen instruments | `data/instruments.csv` | 17 | 17 | ok |
| Abstract, 1, 4.7 | eleven established by term count | `data/instruments.csv` | 11 | 11 | ok |
| 1, 4.7, 5 | six by qualitative reading | `data/instruments.csv` | 6 | 6 | ok |
| 1 | SC-7 contains `duration` exactly once | `data/instruments.csv` | 1 | 1 | ok |
| 1 | SC-7 has 29 control enhancements | `data/instruments.csv` | True | True | ok |
| 1 | SC-7 `duration` refers to a policy-exception lifetime | `data/instruments.csv` | True | True | ok |
| 4.7 | SL5 `containment` twice | `data/instruments.csv` | 2 | 2 | ok |
| 4.7 | SL5 three of four `egress` are electromagnetic | `data/instruments.csv` | 4 | 4 | ok |
| 4.7 | GPAI CoP `containment` zero | `data/instruments.csv` | 0 | 0 | ok |
| 4.7 | Anthropic risk report `egress` once | `data/instruments.csv` | 1 | 1 | ok |
| 4.7 | METR catalogue scores 44 incidents | `data/instruments.csv` | True | True | ok |
| 2 | containment cluster: zero for how long / duration / withstand | `data/instruments.csv` | 0/0/0 | 0/0/0 | ok |
| 4.7, 6 | no instrument records how long a control holds | `data/instruments.csv` | 0 | 0 | ok |
| 4.5 | annual cadence is 8,766 hours | `src/budgets.py -> output/budgets_report.txt` | 8766 | 8766 | ok |
| 4.5 | cadence factor 187 (A1) | `src/budgets.py -> output/budgets_report.txt` | 187 | 187 | ok |
| 4.5 | cadence factor 140 (A2) | `src/budgets.py -> output/budgets_report.txt` | 140 | 140 | ok |
| 4.5 | cadence factor 50 (A3) | `src/budgets.py -> output/budgets_report.txt` | 50 | 50 | ok |
| 4.6 | alert 12:03 UTC on 19 July | `src/budgets.py -> output/budgets_report.txt` | 2026-07-19 12:03 | 2026-07-19 12:03 | ok |
| 4.6 | runs stopped 17:37 UTC | `src/budgets.py -> output/budgets_report.txt` | 2026-07-19 17:37 | 2026-07-19 17:37 | ok |
| 4.6 | 334 minutes | `src/budgets.py -> output/budgets_report.txt` | 334 | 334 | ok |
| 4.6, title | exceeded by a factor of eleven | `src/budgets.py -> output/budgets_report.txt` | 11 | 11 | ok |
| 4.6 | 30-minute false-positive window | `src/budgets.py -> output/budgets_report.txt` | 30 | 30 | ok |
| 4.6 | UK AISI terminated 46 minutes after its alert | `src/budgets.py -> output/budgets_report.txt` | 46 | 46 | ok |
| 4.6 | UK AISI lost 11 h 41 min before the alert | `src/budgets.py -> output/budgets_report.txt` | 11 h 41 min | 11 h 41 min | ok |
| 6 | factor of fifty to a hundred and eighty-seven | `src/budgets.py -> output/budgets_report.txt` | 50-187 | 50-187 | ok |
| 4.4 | Monte Carlo reproduces the ordering in 100 percent of draws | `src/sensitivity.py -> output/sensitivity_report.txt` | True | True | ok |
| 5 | at least 96 transcripts with spoofed tool calls | `data/contradictions.csv W-4` | True | True | ok |
| 5 | roughly 7 percent of those examined | `data/contradictions.csv W-4` | True | True | ok |
| Appendix B | nine contradictions, four in the main text | `data/contradictions.csv` | 9/4 | 9/4 | ok |
| 3 | Twenty-five primary sources | `data/sources.csv` | 25 | 23 P-coded; 26 read in full or in part; 38 primary rows in total | **FAIL** |
| 3 | nine standards or frameworks | `data/sources.csv` | 9 | 11 | **FAIL** |
| 3 | four incident reports read in full | `data/sources.csv` | 4 | 4 | ok |
| 2 | three 2026 containment-verification papers | `data/sources.csv` | 3 | 3 | ok |
| 1, 3 | OpenAI technical report published 26 August 2026 | `data/sources.csv` | 2026-08-26 | 2026-08-26 | ok |
| 4.6 | response budget published 18 August | `data/sources.csv` | 2026-08-18 | 2026-08-18 | ok |
| 4.6 | monitoring post of March 2026 | `data/sources.csv` | 2026-03-19 | 2026-03-19 | ok |
| 4.3 | RubyGems incident disclosed 11 September | `data/sources.csv` | 2026-09-11 | 2026-09-11 | ok |
| 1 | published three weeks after the last public timeline reconstruction | `data/sources.csv` | three weeks | not computable | **unresolved** |
| Abstract | abstract is 149 words, unedited | `paper-text.md` | 149 | 149 | ok |
| throughout | writing rule: no bare P, only P_wall and P_exp | `output/paper.md` | 0 | 0 | ok |
