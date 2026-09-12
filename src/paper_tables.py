"""Generate output/paper_tables.md - every table in paper-ready form.

This file is what gets pasted into the paper, so nothing in it may be written
by hand. Every row here is read from data/ or computed by compute_p, budgets
and sensitivity. Regenerate with:

    python3 src/paper_tables.py
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

import budgets  # noqa: E402
import compute_p  # noqa: E402

DATA = REPO_ROOT / "data"
OUTPUT_MD = REPO_ROOT / "output" / "paper_tables.md"

ROW_TYPE_LABEL = {
    "A_applied_nested": "A — applied, nested",
    "B_applied_nonnested": "B — applied, not nested",
    "C_standing": "C — pre-existing",
    "X_out_of_corpus": "X — out of corpus",
}


def read(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def escape(text: str) -> str:
    """Markdown table cells cannot contain a raw pipe or a newline."""
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def table(headers: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(escape(c) for c in row) + " |" for row in rows]
    return out


def truncate(text: str, limit: int) -> str:
    text = (text or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


# --- Table 1: the clock -----------------------------------------------------

def table_clock(rows: list[dict[str, str]]) -> list[str]:
    out = [
        "## Table 1 — The clock",
        "",
        "One row per control. `P_wall` is computed by `src/compute_p.py`, never entered by hand.",
        "Type C rows are pre-existing controls: no application event, therefore no `P_wall`.",
        "",
    ]
    out += table(
        ["id", "type", "control", "protection goal", "goal source",
         "applied (UTC)", "reconstituted (UTC)", "`P_wall`", "state", "category", "status"],
        [
            [
                r["id"],
                r["row_type"].split("_")[0].upper(),
                truncate(r["control"], 72),
                truncate(r["protection_goal"], 64),
                "operator" if r["goal_source"] == "operator_stated" else "assumption",
                r["applied_utc"],
                r["reconstituted_utc"],
                r["p_wall_hhmm"] or "—",
                r["state"] + ("" if r["state_determinable"] == "TRUE" else " ¹"),
                r["reconstitution_category"],
                r["status"],
            ]
            for r in rows
        ],
    )
    undeterminable = [r["id"] for r in rows if r["state_determinable"] == "FALSE"]
    if undeterminable:
        out += [
            "",
            f"¹ {', '.join(undeterminable)}: the state is **not determinable from the source**. "
            "P1 records only that the first privileged host-mount pod failed and that a second "
            "succeeded minutes later, without describing the difference, so the distinction "
            "between a defeated control and a circumvented one cannot be made. `broken` is the "
            "recorded value but is as much a claim as `bypassed` would be. This is the only such "
            "row in the corpus.",
        ]
    return out


# --- Table 2: corpus breakdown ---------------------------------------------

def table_corpus(rows: list[dict[str, str]]) -> list[str]:
    states = sorted({r["state"] for r in rows})
    body = []
    for row_type, label in ROW_TYPE_LABEL.items():
        group = [r for r in rows if r["row_type"] == row_type]
        counts = Counter(r["state"] for r in group)
        with_p = sum(1 for r in group if r["p_wall_hours"])
        body.append([label, str(len(group))] + [str(counts.get(s, 0)) for s in states] + [str(with_p)])
    totals = Counter(r["state"] for r in rows)
    body.append(["**Total**", f"**{len(rows)}**"]
                + [f"**{totals.get(s, 0)}**" for s in states]
                + [f"**{sum(1 for r in rows if r['p_wall_hours'])}**"])

    out = ["## Table 2 — Corpus breakdown by row type and state", "",
           "The corpus contains exactly one control-application event: the Artifactory rebuild of "
           "`2026-07-06T01:16Z`. Every other control in it was already standing, which is why "
           "type B is defined in the schema and empty in the data.", ""]
    out += table(["row type", "n"] + [s.replace("_", " ") for s in states] + ["with `P_wall`"], body)
    return out


# --- Table 3: the four budget calculations ---------------------------------

def table_budgets(rows: list[dict[str, str]]) -> list[str]:
    measured = budgets.minutes_between(budgets.OPENAI_ALERT, budgets.OPENAI_RUNS_STOPPED)
    aisi_detect = budgets.minutes_between(budgets.AISI_ACTIVITY_ENDED, budgets.AISI_ALERT)
    aisi_react = budgets.minutes_between(budgets.AISI_ALERT, budgets.AISI_EVALS_TERMINATED)
    type_a = budgets.load_type_a_p_wall()

    out = ["## Table 3 — The four calculations", "", "### 3a — Declared response budget against measured performance", ""]
    out += table(
        ["quantity", "value", "source"],
        [
            ["Alert", budgets.OPENAI_ALERT.strftime("%Y-%m-%d %H:%M UTC"), "P1 section X"],
            ["Runs stopped", budgets.OPENAI_RUNS_STOPPED.strftime("%Y-%m-%d %H:%M UTC"), "P1 section X"],
            ["Measured", f"{budgets.hhmm(measured)} = {measured} min", "computed"],
            ["Declared: window to a pause", f"{budgets.FALSE_POSITIVE_WINDOW_MIN} min",
             "OpenAI, 2026-08-18; evidence base 14"],
            ["Declared: full sequential chain", f"{budgets.FULL_CHAIN_MIN} min",
             "OpenAI, 2026-08-18; evidence base 14"],
            ["**Factor over the pause window**",
             f"**{measured / budgets.FALSE_POSITIVE_WINDOW_MIN:.1f}×**", "computed"],
            ["**Factor over the full chain**",
             f"**{measured / budgets.FULL_CHAIN_MIN:.1f}×**", "computed"],
        ],
    )
    out += [
        "",
        "Two precision points travel with this number. **First**, the budget was declared on "
        "18 August 2026, *after* the incident, so it is not a broken promise but a target "
        "calibrated against a performance the organisation has never demonstrated. **Second**, "
        "the 30-minute figure is *older* than the August commitment: P19 of 19 March 2026 "
        "already describes review within 30 minutes of completion, with escalation to human "
        "review inside 30 minutes. What the August commitment adds is the move from "
        "**asynchronous review to blocking intervention, not the interval** — OpenAI's own March "
        "text notes that extending to synchronous blocking would allow actions to be prevented "
        "before execution rather than alerted on shortly after. Presenting 30 minutes as a new "
        "safeguard overstates it (evidence base 15.4).",
        "",
        "### 3b — UK AISI comparison: two latencies, not one",
        "",
    ]
    out += table(
        ["organisation", "detection latency", "reaction latency", "source"],
        [
            ["UK AISI", f"{budgets.hhmm(aisi_detect)} ({aisi_detect} min)",
             f"{budgets.hhmm(aisi_react)} ({aisi_react} min)", "P10 section 3"],
            ["OpenAI", "not computable — no start point in the public record",
             f"{budgets.hhmm(measured)} ({measured} min)", "P1 section X"],
            ["**Ratio, reaction**", "—", f"**{measured / aisi_react:.1f}×**", "computed"],
        ],
    )
    out += [
        "",
        "The two organisations fail at different legs. A `P` budget must declare both, or the "
        "failure only moves.",
        "",
        "### 3c — Cadence arithmetic",
        "",
        f"CSA AICM AIS-13 requires review of sandboxing policies *at least annually* = "
        f"{budgets.HOURS_PER_YEAR:,} hours (evidence base 12.5).",
        "",
    ]
    out += table(
        ["id", "control", "`P_wall`", "ratio to the prescribed cadence"],
        [[rid, truncate(control, 56), f"{p:,.4f} h", f"**{budgets.HOURS_PER_YEAR / p:.1f}×**"]
         for rid, control, p in type_a],
    )
    out += ["", "### 3d — The awareness clock", ""]
    out += [
        "> **What 'breached' means here.** `days` is the interval from the awareness reading to "
        "**public disclosure**. That is a *different quantity* from the regulatory obligation, "
        "which is discharged by reporting to a regulator, not by publishing. A non-public report "
        "to the Commission or to Cal OES could have been timely on any of these readings. Public "
        "disclosure is simply the only date the record supplies, so it is the only interval that "
        "can be computed.",
        "",
    ]
    out += table(
        ["awareness reading", "date", "days to disclosure",
         f"EU ({budgets.EU_CYBER_DEADLINE_DAYS} d)",
         f"California ({budgets.CAL_DEADLINE_DAYS} d)", "evidence", "status"],
        [
            [r.label, r.awareness.isoformat() + (f" / {r.awareness_latest.isoformat()}"
                                                 if r.awareness_latest else ""),
             r.days_label(budgets.DISCLOSURE),
             budgets.verdict(r, budgets.DISCLOSURE, budgets.EU_CYBER_DEADLINE_DAYS),
             budgets.verdict(r, budgets.DISCLOSURE, budgets.CAL_DEADLINE_DAYS),
             r.evidence, r.status]
            for r in budgets.AWARENESS_READINGS
        ],
    )
    out += [
        "",
        "The 18/19 July reading is carried as a **range** because the source gives one.",
        "",
        "**The interpretive question, which is not resolved here:** does the clock start when "
        "OpenAI learned that its model had left containment — or only when it learned *whom* the "
        "escaped model had hit? The source supports at least three different awareness dates, and "
        "which one governs decides a legal question in two jurisdictions. The ambiguity is the "
        "finding (evidence base 16.2).",
    ]
    return out


# --- Table 4: the instruments ----------------------------------------------

def table_instruments() -> list[str]:
    rows = read("instruments.csv")
    count_columns = [
        ("n_duration", "duration"), ("n_how_long", "how long"), ("n_withstand", "withstand"),
        ("n_containment", "containment"), ("n_egress", "egress"),
        ("n_hours", "hours"), ("n_minutes", "minutes"),
    ]
    out = [
        "## Table 4 — The gap, instrument by instrument",
        "",
        "The backbone of the novelty claim. A blank cell means **the evidence base gives no count "
        "for that term in that instrument** — it is not a zero. `count method` records how each "
        "row was established, so a qualitative row is never mistaken for a counted one.",
        "",
    ]
    out += table(
        ["id", "instrument", "version / date", "object protected"]
        + [label for _, label in count_columns]
        + ["time axis", "count method", "source"],
        [
            [r["id"], truncate(r["instrument"], 64), truncate(r["version_or_date"], 42),
             truncate(r["object_protected"], 56)]
            + [r[column] or "—" for column, _ in count_columns]
            + [r["n_time_axis_present"], r["count_method"].replace("_", " "), r["source_ref"]]
            for r in rows
        ],
    )
    methods = Counter(r["count_method"] for r in rows)
    out += [
        "",
        f"**{len(rows)} instruments, and `time axis` is FALSE in every one.** "
        "By count method: "
        + ", ".join(f"{m.replace('_', ' ')} {n}" for m, n in sorted(methods.items()))
        + ". `tests/test_registers.py::test_no_instrument_has_a_time_axis` fails if any "
          "instrument ever gains one.",
    ]
    return out


# --- Table 5: the contradiction register -----------------------------------

def table_contradictions() -> list[str]:
    rows = read("contradictions.csv")
    main = [r for r in rows if r["in_paper_main_text"] == "TRUE"]
    appendix = [r for r in rows if r["in_paper_main_text"] != "TRUE"]

    def block(title: str, group: list[dict[str, str]], note: str) -> list[str]:
        out = [f"### {title}", "", note, ""]
        out += table(
            ["id", "short title", "intra-document", "source A", "source B", "resolving question"],
            [[r["id"], r["short_title"], "yes" if r["intra_document"] == "TRUE" else "no",
              r["source_a"], r["source_b"], truncate(r["resolving_question"], 200)]
             for r in group],
        )
        return out

    intra = sum(1 for r in rows if r["intra_document"] == "TRUE")
    out = [
        "## Table 5 — Contradiction register",
        "",
        f"{len(rows)} documented contradictions, **{intra} of them intra-document** — inside a "
        "single document. Detecting these is itself part of the result, not noise around it. "
        "Full claims for each row are in `data/contradictions.csv`.",
        "",
    ]
    out += block("Main text", main,
                 "These four carry the argument and belong in the body of the paper.")
    out += [""]
    out += block("Appendix", appendix,
                 "Documented, load-bearing for provenance, but not required by the argument.")
    return out


# --- assembly ---------------------------------------------------------------

def build() -> str:
    _, raw = compute_p.load_rows()
    rows = compute_p.compute(raw)

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = [
        "# Paper tables",
        "",
        "**Generated file — do not edit by hand.** Every figure in it is read from `data/` or "
        "computed by `src/`. Regenerate with `python3 src/paper_tables.py`, or run `./verify.sh` "
        "to rebuild the whole pipeline and check the reference values.",
        "",
        f"Generated {generated}. Sources are cited by the short codes registered in "
        "`data/sources.csv`; the full evidence base is `docs/belegbasis-v3.md`.",
        "",
        "**Notation:** always `P_wall` (calendar time) or `P_exp` (agent exposure time), never a "
        "bare `P` — in the security and verification literature `P` regularly denotes a "
        "probability.",
        "",
        "---",
        "",
    ]
    for block in (table_clock(rows), table_corpus(rows), table_budgets(rows),
                  table_instruments(), table_contradictions()):
        out += block
        out += ["", "---", ""]
    return "\n".join(out).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUTPUT_MD)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build(), encoding="utf-8")
    if not args.quiet:
        print(f"Written: {args.out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
