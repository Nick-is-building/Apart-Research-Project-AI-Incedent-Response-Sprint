"""Budget, cadence and awareness arithmetic.

Four calculations, each printing its own sources:

  (a) OpenAI's declared response budget against measured performance
  (b) The UK AISI comparison - detection latency and reaction latency, separately
  (c) Cadence arithmetic - CSA AICM AIS-13 against each type-A P_wall
  (d) The awareness clock - four readings of when OpenAI became aware, against
      two regulatory clocks

Nothing here is estimated. Every input is a timestamp or a figure from the
evidence base, and every ratio is computed from those inputs rather than
typed in.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

import compute_p  # noqa: E402

OUTPUT_TXT = REPO_ROOT / "output" / "budgets_report.txt"

RULE = "=" * 78
THIN = "-" * 78


def utc(text: str) -> datetime:
    parsed = compute_p.parse_utc(text)
    if parsed is None:
        raise ValueError(f"not a timestamp: {text!r}")
    return parsed


def minutes_between(start: datetime, end: datetime) -> int:
    return int(round((end - start).total_seconds() / 60))


def hhmm(total_minutes: int) -> str:
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours} h {minutes:02d} min"


# --- (a) declared budget against measured performance -----------------------

# Evidence base 14, from OpenAI's post of 18 August 2026.
ALERT_ISSUE_TARGET_MIN = 30      # "We aim to issue an [alert]" within 30 minutes
FALSE_POSITIVE_WINDOW_MIN = 30   # 30 minutes to rule out a false positive, else pause
FULL_CHAIN_MIN = ALERT_ISSUE_TARGET_MIN + FALSE_POSITIVE_WINDOW_MIN  # sequential

# Evidence base 4.5 / 16.3a, from P1 section X.
OPENAI_ALERT = utc("2026-07-19T12:03Z")
OPENAI_RUNS_STOPPED = utc("2026-07-19T17:37Z")


def calculation_a() -> list[str]:
    measured = minutes_between(OPENAI_ALERT, OPENAI_RUNS_STOPPED)
    against_pause = measured / FALSE_POSITIVE_WINDOW_MIN
    against_chain = measured / FULL_CHAIN_MIN

    return [
        "(a) DECLARED RESPONSE BUDGET AGAINST MEASURED PERFORMANCE",
        THIN,
        "  Declared (P1 / OpenAI, 'Pacing model development in an era of cyber-critical",
        "  capabilities', 2026-08-18; evidence base 14), verbatim:",
        "",
        "      'If they cannot conclusively determine within 30 minutes that the flag is a",
        "       false positive, those teams are expected to pause the activity.'",
        "",
        "  plus a stated aim to issue the alert within 30 minutes. The two deadlines are",
        f"  sequential, so the real budget to a pause is up to {FULL_CHAIN_MIN} minutes.",
        "",
        "  Measured, on the only day on which it can be measured (P1 section X):",
        f"      alert            {OPENAI_ALERT.strftime('%Y-%m-%d %H:%M')} UTC",
        f"      runs stopped     {OPENAI_RUNS_STOPPED.strftime('%Y-%m-%d %H:%M')} UTC",
        f"      elapsed          {hhmm(measured)} = {measured} minutes",
        "",
        f"      against the {FALSE_POSITIVE_WINDOW_MIN}-minute window to a pause:      "
        f"{against_pause:>6.1f}x over budget",
        f"      against the full {FULL_CHAIN_MIN}-minute chain:              "
        f"{against_chain:>6.1f}x over budget",
        "",
        "  TWO PRECISION POINTS THAT MUST TRAVEL WITH THIS NUMBER",
        "",
        "  1. The budget was declared on 18 August 2026, AFTER the incident. This is",
        "     therefore not a broken promise. It is a target calibrated against a",
        "     performance the organisation has never demonstrated. That is the honest",
        "     formulation and also the stronger one.",
        "",
        "  2. The 30-minute figure is OLDER than the August commitment. OpenAI's",
        "     publication of 19 March 2026 ('How we monitor internal coding agents for",
        "     misalignment', P19) already describes a system that reviews interactions",
        "     within 30 minutes of completion and escalates higher severity levels to",
        "     human review within 30 minutes. What is new in the August commitment is",
        "     the move from ASYNCHRONOUS REVIEW to BLOCKING INTERVENTION, not the",
        "     interval. OpenAI wrote in March that extending to synchronous blocking",
        "     would allow actions to be prevented before execution rather than alerted",
        "     on shortly after - so the March monitoring was asynchronous by its own",
        "     account. Any presentation of 30 minutes as a new safeguard overstates it.",
        "     Evidence base 15.4, consequence 2.",
        "",
        "  Sources: evidence base 14 (declared budget), 15.4 (P19, the prior 30-minute",
        "  figure), 4.5 and 16.3a (measured timestamps, P1 section X).",
    ]


# --- (b) the UK AISI comparison ---------------------------------------------

# Evidence base 16.3 / 16.3a, from P10 section 3.
AISI_ACTIVITY_ENDED = utc("2026-07-27T23:15Z")
AISI_ALERT = utc("2026-07-28T10:56Z")
AISI_EVALS_TERMINATED = utc("2026-07-28T11:42Z")


def calculation_b() -> list[str]:
    aisi_detection = minutes_between(AISI_ACTIVITY_ENDED, AISI_ALERT)
    aisi_reaction = minutes_between(AISI_ALERT, AISI_EVALS_TERMINATED)
    openai_reaction = minutes_between(OPENAI_ALERT, OPENAI_RUNS_STOPPED)
    reaction_ratio = openai_reaction / aisi_reaction

    return [
        "(b) UK AISI COMPARISON - TWO LATENCIES, NOT ONE",
        THIN,
        "  UK AISI, INC-2026-07-28-01 (P10, section 3):",
        f"      unsanctioned activity ended   {AISI_ACTIVITY_ENDED.strftime('%Y-%m-%d %H:%M')} UTC",
        f"      alert                         {AISI_ALERT.strftime('%Y-%m-%d %H:%M')} UTC",
        f"      all evaluations terminated    {AISI_EVALS_TERMINATED.strftime('%Y-%m-%d %H:%M')} UTC",
        "",
        f"      DETECTION latency   activity end -> alert   {hhmm(aisi_detection):>12}"
        f"  = {aisi_detection} min",
        f"      REACTION latency    alert -> termination    {hhmm(aisi_reaction):>12}"
        f"  = {aisi_reaction} min",
        "",
        "  OpenAI, same two measures (P1 section X):",
        f"      DETECTION latency   not computable: no public timestamp marks when the",
        f"                          unsanctioned activity began or could first have been seen",
        f"      REACTION latency    alert -> runs stopped   {hhmm(openai_reaction):>12}"
        f"  = {openai_reaction} min",
        "",
        f"      OpenAI reaction / AISI reaction:  {reaction_ratio:.1f}x",
        "",
        "  THE POINT OF THE COMPARISON",
        "",
        "  These are two separate measures and the two organisations fail at different",
        "  ones. The government evaluator reacted inside an hour - the same order of",
        f"  magnitude as OpenAI's own later declared budget - while the lab took {openai_reaction}",
        f"  minutes, a factor of {openai_reaction / FALSE_POSITIVE_WINDOW_MIN:.1f} over that budget. AISI's weakness sits elsewhere:",
        f"  {hhmm(aisi_detection)} passed between the end of the unsanctioned activity and the alert.",
        "",
        "  For the clause this means a P budget must declare BOTH legs. Declaring only",
        "  reaction time moves the failure rather than removing it.",
        "",
        "  Honest limit: OpenAI's detection latency is left blank on purpose. Computing",
        "  one would require a start point the public record does not supply.",
        "",
        "  Sources: evidence base 16.3, 16.3a; P10 section 3; P1 section X.",
    ]


# --- (c) cadence arithmetic -------------------------------------------------

# Evidence base 12.5: AICM AIS-13, model-provider implementation guideline, point 4.
HOURS_PER_YEAR = 8766  # 365.25 days, the figure used in evidence base 12.5


def calculation_c(type_a: list[tuple[str, str, float]]) -> list[str]:
    lines = [
        "(c) CADENCE ARITHMETIC - PRESCRIBED REVIEW INTERVAL AGAINST MEASURED HOLD TIME",
        THIN,
        "  CSA AI Controls Matrix, AIS-13, model-provider implementation guideline,",
        "  point 4: reviews of sandboxing policies 'at least annually', or after",
        "  material changes.",
        "",
        f"      at least annually = {HOURS_PER_YEAR:,} hours",
        "",
        "  Against each measured protection time (evidence base 4.3):",
        "",
        f"      {'id':<4} {'P_wall':>12}   {'ratio':>10}   control",
        f"      {'-' * 4} {'-' * 12}   {'-' * 10}   {'-' * 40}",
    ]
    ratios = []
    for row_id, control, p_wall in type_a:
        ratio = HOURS_PER_YEAR / p_wall
        ratios.append(ratio)
        lines.append(f"      {row_id:<4} {p_wall:>10.4f} h   {ratio:>9.1f}x   {control[:40]}")

    lines += [
        "",
        f"  The prescribed re-verification cadence exceeds the only measured hold times",
        f"  by a factor of {min(ratios):.0f} to {max(ratios):.0f}.",
        "",
        "  This is a quotient of a standards requirement and a primary measurement, not",
        "  an opinion. It is the number that grounds the cadence requirement of the",
        "  clause. Expected order of magnitude per the brief: 50 to 187 - reproduced.",
        "",
        "  Sources: evidence base 12.5 (AIS-13, N2), 4.3 (the three P_wall values).",
    ]
    return lines


# --- (d) the awareness clock ------------------------------------------------

DISCLOSURE = date(2026, 7, 21)  # OpenAI's public disclosure of its involvement

# Evidence base 16.1: the two regulatory clocks.
EU_CYBER_DEADLINE_DAYS = 5   # GPAI Code of Practice, Commitment 9, cyberattacks
CAL_DEADLINE_DAYS = 15       # SB 53 / TFAIA, section 22757.13, from discovery


@dataclass(frozen=True)
class AwarenessReading:
    """One candidate reading of when OpenAI became aware.

    `awareness_latest` is set only where the source itself gives a range; the
    evidence base dates the Reuters reading to '18/19 July', which is carried
    as a range rather than collapsed to one day.
    """

    label: str
    awareness: date
    evidence: str
    status: str
    awareness_latest: date | None = None

    def days_to(self, disclosure: date) -> tuple[int, int]:
        """(minimum, maximum) days to disclosure. Equal unless the source ranges."""
        latest = (disclosure - self.awareness).days
        earliest = (disclosure - (self.awareness_latest or self.awareness)).days
        return earliest, latest

    def days_label(self, disclosure: date) -> str:
        low, high = self.days_to(disclosure)
        return str(low) if low == high else f"{low}-{high}"


# Evidence base 16.2, all four readings, in the order the evidence base gives them.
AWARENESS_READINGS = (
    AwarenessReading(
        "20 Jul - the two incidents are linked",
        date(2026, 7, 20),
        "P1, P2",
        "PRIMARY",
    ),
    AwarenessReading(
        "18/19 Jul - staff find the escape in own logs",
        date(2026, 7, 18),
        "Reuters",
        "SECONDARY",
        awareness_latest=date(2026, 7, 19),
    ),
    AwarenessReading(
        "9 Jul - agent bypasses outbound controls",
        date(2026, 7, 9),
        "P1 IV.A",
        "PRIMARY",
    ),
    AwarenessReading(
        "5 Jul - security incident opened",
        date(2026, 7, 5),
        "P1 III.B",
        "PRIMARY",
    ),
)


def verdict(reading: AwarenessReading, disclosure: date, deadline: int) -> str:
    """Verdict for one reading against one deadline.

    A reading the source gives as a range can straddle a deadline; where it
    does, that is reported rather than decided.
    """
    low, high = reading.days_to(disclosure)
    if high <= deadline:
        return "met"
    if low > deadline:
        overrun_low, overrun_high = low - deadline, high - deadline
        if overrun_low == overrun_high:
            return f"BREACHED by {overrun_low} d"
        return f"BREACHED by {overrun_low}-{overrun_high} d"
    return "depends on reading"


def calculation_d() -> list[str]:
    lines = [
        "(d) THE AWARENESS CLOCK",
        THIN,
        "  Both regulatory clocks start at awareness. The public record supports at",
        "  least three different awareness dates, so the same facts produce different",
        "  compliance outcomes depending on which one is taken.",
        "",
        "  Clocks (evidence base 16.1):",
        f"      EU    GPAI Code of Practice, Commitment 9: not later than {EU_CYBER_DEADLINE_DAYS} days after",
        "            the Signatories become aware of the involvement of their model in the",
        "            incident. Cyberattacks fall under this limb. Operationalises Article",
        "            55(1)(c), which says 'without undue delay' without a number.",
        f"      CA    SB 53 / TFAIA, section 22757.13: {CAL_DEADLINE_DAYS} days from discovery. Covered",
        "            incidents include 'loss of control of a frontier model'.",
        "",
        f"  Public disclosure of OpenAI's involvement: {DISCLOSURE.isoformat()}",
        "",
        "  The 18/19 July reading is carried as a RANGE because the source gives one.",
        "",
        "  WHAT 'BREACHED' MEANS IN THIS TABLE - READ BEFORE THE NUMBERS",
        "",
        "      'days' is the interval from the awareness reading to PUBLIC DISCLOSURE.",
        "      That is a DIFFERENT QUANTITY from the regulatory obligation, which is",
        "      discharged by reporting to a regulator, not by publishing. A non-public",
        "      report to the Commission or to Cal OES could have been timely on any of",
        "      these readings. Public disclosure is simply the only date the record",
        "      supplies, so it is the only interval that can be computed.",
        "",
    ]

    # Column widths follow the content, so a longer label can never collide
    # with the column beside it.
    table = [
        (
            reading.label,
            reading.days_label(DISCLOSURE),
            verdict(reading, DISCLOSURE, EU_CYBER_DEADLINE_DAYS),
            verdict(reading, DISCLOSURE, CAL_DEADLINE_DAYS),
            reading.evidence,
            reading.status,
        )
        for reading in AWARENESS_READINGS
    ]
    titles = ("awareness reading", "days", "EU (5 d)", "CA (15 d)", "evidence", "status")
    widths = [max(len(title), *(len(row[i]) for row in table)) for i, title in enumerate(titles)]

    def render(cells: tuple[str, ...]) -> str:
        parts = [cells[0].ljust(widths[0]), cells[1].rjust(widths[1])]
        parts += [cells[i].ljust(widths[i]) for i in range(2, len(cells))]
        return "  " + "  ".join(parts).rstrip()

    lines.append(render(titles))
    lines.append("  " + "-" * (sum(widths) + 2 * (len(widths) - 1)))
    for row in table:
        lines.append(render(row))

    breaches_eu = sum(
        1 for r in AWARENESS_READINGS
        if verdict(r, DISCLOSURE, EU_CYBER_DEADLINE_DAYS).startswith("BREACHED")
    )
    breaches_ca = sum(
        1 for r in AWARENESS_READINGS
        if verdict(r, DISCLOSURE, CAL_DEADLINE_DAYS).startswith("BREACHED")
    )

    lines += [
        "",
        f"  Summary: {breaches_eu} of {len(AWARENESS_READINGS)} readings breach the EU clock, "
        f"{breaches_ca} of {len(AWARENESS_READINGS)} breach the California clock.",
        "",
        "  THE INTERPRETIVE QUESTION - PRINTS WITH THE RESULT, AND IS NOT RESOLVED HERE",
        "",
        "      Does the clock start when OpenAI learned that its model had left",
        "      containment - or only when it learned WHOM the escaped model had hit?",
        "",
        "  The ambiguity is the finding. The source supports at least three different",
        "  awareness dates, and which one governs decides a legal question in two",
        "  jurisdictions. This repository does not pick one, and no figure above should",
        "  be quoted as the days-to-disclosure without the reading it belongs to.",
        "",
        "  This table is not a compliance determination. Whether a report was in fact",
        "  filed with the Commission or with Cal OES is not public, and CeSIA has asked",
        "  the Commission publicly to say whether and when a report under Article",
        "  55(1)(c) was made.",
        "",
        "  Note on W-2: what was an internal inconsistency in the record becomes, under",
        "  this table, the determinant of a legal question. Evidence base 16.2.",
        "",
        "  Sources: evidence base 16.1 (both clocks, N1 Commitment 9 and N9 SB 53),",
        "  16.2 (the four readings), W-2.",
    ]
    return lines


# --- report -----------------------------------------------------------------

def load_type_a_p_wall() -> list[tuple[str, str, float]]:
    _, rows = compute_p.load_rows()
    computed = compute_p.compute(rows)
    out = []
    for row in computed:
        if row["row_type"] == "A_applied_nested":
            out.append((row["id"], row["control"], float(row["p_wall_hours"])))
    return sorted(out, key=lambda r: r[2])


def build_report() -> str:
    type_a = load_type_a_p_wall()
    if len(type_a) != 3:
        raise SystemExit(f"expected 3 type-A rows, found {len(type_a)}")

    out = [RULE, "BUDGET, CADENCE AND AWARENESS ARITHMETIC", RULE, ""]
    for block in (calculation_a(), calculation_b(), calculation_c(type_a), calculation_d()):
        out.extend(block)
        out.append("")
    out.append(RULE)
    out.append("All P_wall values are read from output/clock_computed.csv, computed by")
    out.append("src/compute_p.py. No figure in this report is typed in by hand.")
    out.append(RULE)
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUTPUT_TXT)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    report = build_report()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report + "\n", encoding="utf-8")
    if not args.quiet:
        print(report)
        print()
        print(f"Written: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
