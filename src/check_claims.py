"""Trace every quantitative claim in the paper back to a file in the repository.

Writes output/paper_claims_check.md. Each claim names the file it should come
from, the value the repository yields when recomputed, and whether the two
agree. Claims that do not reproduce are reported, never reconciled.
"""

from __future__ import annotations

import argparse
import collections
import csv
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

import budgets  # noqa: E402
import compute_p  # noqa: E402
import instruments_summary  # noqa: E402

PAPER = REPO_ROOT / "output" / "paper.md"
OUTPUT_MD = REPO_ROOT / "output" / "paper_claims_check.md"

OK = "reproduces"
FAIL = "DOES NOT REPRODUCE"
UNRESOLVED = "not resolvable to a file"


@dataclass
class Claim:
    section: str
    claim: str
    source: str
    expected: str
    actual: str
    status: str
    note: str = ""


def read_csv(name: str) -> list[dict[str, str]]:
    with (REPO_ROOT / "data" / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def check(section: str, text: str, source: str, expected: object, actual: object,
          note: str = "") -> Claim:
    expected_s, actual_s = str(expected), str(actual)
    status = OK if expected_s == actual_s else FAIL
    return Claim(section, text, source, expected_s, actual_s, status, note)


def collect() -> list[Claim]:
    clock = compute_p.compute(compute_p.load_rows()[1])
    by_id = {r["id"]: r for r in clock}
    instruments_all = read_csv("instruments.csv")
    instruments = instruments_summary.instrument_rows(instruments_all)
    counted, qualitative, _ = instruments_summary.tally(instruments_all)
    sources = read_csv("sources.csv")
    contradictions = read_csv("contradictions.csv")

    measured = budgets.minutes_between(budgets.OPENAI_ALERT, budgets.OPENAI_RUNS_STOPPED)
    aisi_detect = budgets.minutes_between(budgets.AISI_ACTIVITY_ENDED, budgets.AISI_ALERT)
    aisi_react = budgets.minutes_between(budgets.AISI_ALERT, budgets.AISI_EVALS_TERMINATED)
    year = budgets.HOURS_PER_YEAR

    C = []
    D = "data/clock.csv -> output/clock_computed.csv"
    I = "data/instruments.csv"
    S = "data/sources.csv"

    # --- the three protection times, quoted in abstract, 4.1, 5, 6 ---------
    for rid, value in (("A1", "46 h 50 min"), ("A2", "62 h 45 min"), ("A3", "175 h 30 min")):
        C.append(check("Abstract, 4.1", f"{rid} protection time {value}", D,
                       value, by_id[rid]["p_wall_hhmm"]))
    C.append(check("Abstract, 3, 4.1", "single control application at 2026-07-06 01:16 UTC", D,
                   "2026-07-06T01:16Z", by_id["A1"]["applied_utc"]))
    C.append(check("4.1", "realisation 2026-07-08 00:06 UTC (egress)", D,
                   "2026-07-08T00:06Z", by_id["A1"]["reconstituted_utc"]))
    C.append(check("4.1", "realisation 2026-07-08 16:01 UTC (inter-agent)", D,
                   "2026-07-08T16:01Z", by_id["A2"]["reconstituted_utc"]))
    C.append(check("4.1", "realisation 2026-07-13 08:46 UTC (admin)", D,
                   "2026-07-13T08:46Z", by_id["A3"]["reconstituted_utc"]))
    C.append(check("4.1", "control held: HTTP 400 at 2026-07-06 12:56 UTC", D,
                   "2026-07-06T12:56Z", by_id["A1"]["held_evidence_utc"]))
    C.append(check("4.2, Abstract", "all three controls bypassed, none broken", D,
                   "bypassed x3",
                   "bypassed x%d" % sum(1 for r in clock
                                        if r["row_type"] == "A_applied_nested"
                                        and r["state"] == "bypassed")))
    C.append(check("5", "rounded to 47, 63 and 176 hours", D, "47/63/176",
                   "/".join(str(round(float(by_id[i]["p_wall_hours"])))
                            for i in ("A1", "A2", "A3"))))

    # --- corpus shape -------------------------------------------------------
    C.append(check("3", "sixteen of the twenty-two rows are standing controls", D,
                   "16 of 22",
                   "%d of %d" % (sum(1 for r in clock if r["row_type"] == "C_standing"),
                                 len(clock))))
    C.append(check("3", "exactly one control-application event", D, 1,
                   len({r["applied_utc"] for r in clock} - {"PRE_EXISTING"})))
    C.append(check("4.3", "three out-of-corpus rows, three separate incidents", D, 3,
                   sum(1 for r in clock if r["row_type"] == "X_out_of_corpus")))
    C.append(check("5", "one row's state not determinable from the source", D, 1,
                   sum(1 for r in clock if r["state_determinable"] == "FALSE")))
    C.append(check("5", "five egress controls at Hugging Face", D, 5,
                   sum(1 for r in clock if r["id"] in ("C10", "C11", "C12", "C13", "C14"))))

    # --- instruments --------------------------------------------------------
    C.append(check("Abstract, 1, 4.7, 6", "seventeen instruments", I, 17, len(instruments)))
    C.append(check("Abstract, 1, 4.7", "eleven established by term count", I, 11, counted))
    C.append(check("1, 4.7, 5", "six by qualitative reading", I, 6, qualitative))
    i06 = next(r for r in instruments if r["id"] == "I06")
    C.append(check("1", "SC-7 contains `duration` exactly once", I, "1", i06["n_duration"]))
    C.append(check("1", "SC-7 has 29 control enhancements", I, True,
                   "29 control enhancements" in i06["version_or_date"],
                   "string match in version_or_date"))
    C.append(check("1", "SC-7 `duration` refers to a policy-exception lifetime", I, True,
                   "administrative exception" in i06["scope_note"], "string match"))
    i02 = next(r for r in instruments if r["id"] == "I02")
    C.append(check("4.7", "SL5 `containment` twice", I, "2", i02["n_containment"]))
    C.append(check("4.7", "SL5 three of four `egress` are electromagnetic", I, "4",
                   i02["n_egress"], "total is 4; the 3-of-4 split is in scope_note"))
    i03 = next(r for r in instruments if r["id"] == "I03")
    C.append(check("4.7", "GPAI CoP `containment` zero", I, "0", i03["n_containment"]))
    i11 = next(r for r in instruments if r["id"] == "I11")
    C.append(check("4.7", "Anthropic risk report `egress` once", I, "1", i11["n_egress"]))
    i17 = next(r for r in instruments if r["id"] == "I17")
    C.append(check("4.7", "METR catalogue scores 44 incidents", I, True,
                   "44 incidents" in i17["version_or_date"], "string match"))
    C.append(check("2", "containment cluster: zero for how long / duration / withstand", I,
                   "0/0/0",
                   "/".join(next(r for r in instruments if r["id"] == cv)[col]
                            for cv, col in (("I12", "n_how_long"), ("I13", "n_duration"),
                                            ("I14", "n_withstand")))))
    C.append(check("4.7, 6", "no instrument records how long a control holds", I, 0,
                   sum(1 for r in instruments if r["n_time_axis_present"] != "FALSE")))

    # --- budgets and cadence ------------------------------------------------
    B = "src/budgets.py -> output/budgets_report.txt"
    C.append(check("4.5", "annual cadence is 8,766 hours", B, 8766, year))
    for rid, factor in (("A1", 187), ("A2", 140), ("A3", 50)):
        C.append(check("4.5", f"cadence factor {factor} ({rid})", B, factor,
                       round(year / float(by_id[rid]["p_wall_hours"]))))
    C.append(check("4.6", "alert 12:03 UTC on 19 July", B, "2026-07-19 12:03",
                   budgets.OPENAI_ALERT.strftime("%Y-%m-%d %H:%M")))
    C.append(check("4.6", "runs stopped 17:37 UTC", B, "2026-07-19 17:37",
                   budgets.OPENAI_RUNS_STOPPED.strftime("%Y-%m-%d %H:%M")))
    C.append(check("4.6", "334 minutes", B, 334, measured))
    C.append(check("4.6, title", "exceeded by a factor of eleven", B, 11,
                   round(measured / budgets.FALSE_POSITIVE_WINDOW_MIN)))
    C.append(check("4.6", "30-minute false-positive window", B, 30,
                   budgets.FALSE_POSITIVE_WINDOW_MIN))
    C.append(check("4.6", "UK AISI terminated 46 minutes after its alert", B, 46, aisi_react))
    C.append(check("4.6", "UK AISI lost 11 h 41 min before the alert", B, "11 h 41 min",
                   budgets.hhmm(aisi_detect)))
    C.append(check("6", "factor of fifty to a hundred and eighty-seven", B, "50-187",
                   "%d-%d" % (round(year / float(by_id["A3"]["p_wall_hours"])),
                              round(year / float(by_id["A1"]["p_wall_hours"])))))

    # --- sensitivity --------------------------------------------------------
    C.append(check("4.4", "Monte Carlo reproduces the ordering in 100 percent of draws",
                   "src/sensitivity.py -> output/sensitivity_report.txt", True,
                   "held in: 100.00% of draws" in
                   (REPO_ROOT / "output" / "sensitivity_report.txt").read_text(encoding="utf-8"),
                   "string match in the generated report"))

    # --- transcript integrity ----------------------------------------------
    w4 = next(r for r in contradictions if r["id"] == "W-4")
    C.append(check("5", "at least 96 transcripts with spoofed tool calls",
                   "data/contradictions.csv W-4", True, "96 transcripts" in w4["claim_b"],
                   "string match"))
    C.append(check("5", "roughly 7 percent of those examined",
                   "data/contradictions.csv W-4", True, "7 percent" in w4["claim_b"],
                   "string match"))
    C.append(check("Appendix B", "nine contradictions, four in the main text",
                   "data/contradictions.csv", "9/4",
                   "%d/%d" % (len(contradictions),
                              sum(1 for r in contradictions
                                  if r["in_paper_main_text"] == "TRUE"))))

    # --- sources ------------------------------------------------------------
    kinds = collections.Counter(r["kind"] for r in sources)
    p_coded = [r["key"] for r in sources if re.fullmatch(r"P\d+", r["key"])]
    C.append(check("3", "twenty-three primary sources", S, 23, len(p_coded),
                   "P-coded entries in the register"))
    C.append(check("3", "eleven standards or frameworks", S, 11, kinds["framework"],
                   "rows with kind=framework, N1-N11"))
    C.append(check("3", "four incident reports read in full", S, 4,
                   sum(1 for r in sources if r["key"] in ("P1", "P2", "P3", "P4")
                       and r["read_status"] == "read_in_full")))
    C.append(check("2", "three 2026 containment-verification papers", S, 3,
                   sum(1 for r in sources if r["key"].startswith("CV"))))
    C.append(check("1, 3", "OpenAI technical report published 26 August 2026", S,
                   "2026-08-26", next(r["date"] for r in sources if r["key"] == "P1")))
    C.append(check("4.6", "response budget published 18 August", S, "2026-08-18",
                   next(r["date"] for r in sources if r["key"] == "S03")))
    C.append(check("4.6", "monitoring post of March 2026", S, "2026-03-19",
                   next(r["date"] for r in sources if r["key"] == "P19")))
    C.append(check("4.3", "RubyGems incident disclosed 11 September", S, "2026-09-11",
                   next(r["date"] for r in sources if r["key"] == "P25")))

    import datetime

    reconstruction = datetime.date(2026, 8, 7)   # P23, LessWrong, 7 August 2026
    appendix_published = datetime.date(2026, 8, 26)  # P1
    C.append(check("1", "nineteen days after the most detailed public timeline reconstruction",
                   S, 19, (appendix_published - reconstruction).days,
                   "P23 dated 2026-08-07 against P1 dated 2026-08-26. Note: the register "
                   "attributes the 7 August reconstruction to Boyd Kane, not to Willison."))
    C.append(check("1", "the reconstruction was built from the Black Hat talk", S, True,
                   next(r["date"] for r in sources if r["key"] == "P4").startswith("2026-08-05"),
                   "P4 talk 5 August precedes the 7 August reconstruction"))

    # --- abstract and writing rule -----------------------------------------
    paper = PAPER.read_text(encoding="utf-8")
    abstract = paper[paper.index("## Abstract"):paper.index("## 1. Introduction")]
    abstract_body = abstract.split("---")[0].replace("## Abstract", "").strip()
    C.append(check("Abstract", "abstract is 149 words, unedited",
                   "paper-text.md", 149, len(abstract_body.split())))

    stripped = re.sub(r"```.*?```", "", paper, flags=re.S)
    stripped = re.sub(r"`[^`]*`", "", stripped)
    stripped = re.sub(r"\bP\d+\b", "", stripped)
    bare = re.findall(r"(?<![\w_])P(?![\w_])", stripped)
    C.append(check("throughout", "writing rule: no bare P, only P_wall and P_exp",
                   "output/paper.md", 0, len(bare)))

    return C


def build_report(claims: list[Claim]) -> str:
    failing = [c for c in claims if c.status == FAIL]
    unresolved = [c for c in claims if c.status == UNRESOLVED]
    passing = [c for c in claims if c.status == OK]

    out = [
        "# Paper claims check",
        "",
        "**Generated file — do not edit by hand.** Regenerate with "
        "`python3 src/check_claims.py`.",
        "",
        "Every quantitative claim in `output/paper.md` is listed with the file it should trace "
        "to and the value the repository yields when that file is recomputed. Claims that do "
        "not reproduce are reported here, not reconciled: where the prose and the data "
        "disagree, the disagreement is the finding.",
        "",
        f"**{len(passing)} of {len(claims)} claims reproduce.** "
        f"{len(failing)} do not. {len(unresolved)} cannot be resolved to a file.",
        "",
    ]

    if failing or unresolved:
        out += ["## Claims requiring attention", ""]
        for c in failing + unresolved:
            out += [
                f"### {c.status} — §{c.section}: {c.claim}",
                "",
                f"- **Source:** `{c.source}`",
                f"- **Paper says:** {c.expected}",
                f"- **Repository yields:** {c.actual}",
            ]
            if c.note:
                out += [f"- **Note:** {c.note}"]
            out += [""]
        out += ["---", ""]

    out += ["## All claims", "",
            "| § | Claim | Source | Paper | Repository | Result |",
            "|---|---|---|---|---|---|"]
    for c in claims:
        mark = {OK: "ok", FAIL: "**FAIL**", UNRESOLVED: "**unresolved**"}[c.status]
        out.append(f"| {c.section} | {c.claim} | `{c.source}` | {c.expected} | {c.actual} "
                   f"| {mark} |")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUTPUT_MD)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    claims = collect()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build_report(claims), encoding="utf-8")

    failing = [c for c in claims if c.status != OK]
    if not args.quiet:
        print(f"Written: {args.out.relative_to(REPO_ROOT)}")
        print(f"  {len(claims) - len(failing)} of {len(claims)} claims reproduce")
        for c in failing:
            print(f"  {c.status}  §{c.section}: {c.claim}")
            print(f"       paper: {c.expected}   repository: {c.actual}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
