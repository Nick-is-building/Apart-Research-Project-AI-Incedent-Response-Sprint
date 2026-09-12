"""Compute protection time P_wall from data/clock.csv.

P_wall is the calendar time from the application of a control to the first
successful realisation of the blocked capability by any mechanism.

Two rules govern this module and are the reason it exists at all:

  1. P_wall is computed, never typed in by hand.  The evidence base states
     target values for the three type-A rows; tests/test_values.py checks that
     this code reproduces them exactly.

  2. Type C rows (pre-existing controls) get no P_wall.  They were never
     applied, so there is no application event and no interval.  Computing a
     duration for them would be a substantive error, not a formatting one.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLOCK_CSV = REPO_ROOT / "data" / "clock.csv"
OUTPUT_CSV = REPO_ROOT / "output" / "clock_computed.csv"

# Row types for which P_wall is defined at all.
COMPUTABLE_ROW_TYPES = frozenset({"A_applied_nested", "B_applied_nonnested"})

# Sentinel values that may stand in a timestamp column.
NOT_DATED = "NOT_DATED"
NEVER = "NEVER"
PRE_EXISTING = "PRE_EXISTING"
SENTINELS = frozenset({NOT_DATED, NEVER, PRE_EXISTING, ""})

COMPUTED_COLUMNS = ["p_wall_hours", "p_wall_hhmm"]


@dataclass(frozen=True)
class Interval:
    """A computed protection time."""

    hours: float
    hhmm: str


def parse_utc(value: str) -> datetime | None:
    """Parse an ISO-8601 UTC timestamp of the form 2026-07-06T01:16Z.

    Returns None for sentinels and for anything that is not a valid timestamp.
    Never raises: an unparseable value means "no measurement", not a crash.
    """
    value = (value or "").strip()
    if value in SENTINELS:
        return None
    try:
        # datetime.fromisoformat accepts "+00:00" but not the "Z" suffix
        # before Python 3.11; normalising keeps this working either way.
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def to_hhmm(total_minutes: int) -> str:
    """Format whole minutes as 'H h MM min'. Hours are not wrapped at 24."""
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours} h {minutes:02d} min"


def compute_interval(applied: datetime, reconstituted: datetime) -> Interval:
    delta = reconstituted - applied
    total_minutes = int(round(delta.total_seconds() / 60))
    return Interval(hours=delta.total_seconds() / 3600.0, hhmm=to_hhmm(total_minutes))


def reason_not_computed(row: dict[str, str]) -> str | None:
    """Why this row carries no P_wall, or None if it should carry one."""
    row_type = row["row_type"]
    applied_raw = (row["applied_utc"] or "").strip()
    reconstituted_raw = (row["reconstituted_utc"] or "").strip()

    if row_type == "C_standing":
        return (
            "type C (pre-existing control): no application event, therefore no "
            "P_wall by definition; measured binarily instead"
        )
    if row_type not in COMPUTABLE_ROW_TYPES:
        return f"row type {row_type} is outside the measured corpus"
    if applied_raw == PRE_EXISTING:
        return "applied_utc is PRE_EXISTING: no application event"
    if reconstituted_raw == NEVER:
        return "reconstituted_utc is NEVER: the blocked capability was never realised"
    if reconstituted_raw == NOT_DATED:
        return "reconstituted_utc is NOT_DATED: no dated reconstitution in the sources"
    if parse_utc(applied_raw) is None:
        return f"applied_utc is not a valid ISO-8601 timestamp: {applied_raw!r}"
    if parse_utc(reconstituted_raw) is None:
        return f"reconstituted_utc is not a valid ISO-8601 timestamp: {reconstituted_raw!r}"
    return None


def append_note(existing: str, addition: str) -> str:
    existing = (existing or "").strip()
    if not existing:
        return addition
    if addition in existing:
        return existing
    separator = " " if existing.endswith(".") else ". "
    return f"{existing}{separator}{addition}"


def validate_applied_utc(rows: list[dict[str, str]]) -> None:
    """applied_utc is an ISO-8601 UTC timestamp or PRE_EXISTING. Nothing else.

    The corpus contains exactly one control-application event, the Artifactory
    rebuild of 2026-07-06T01:16Z.  Every other control in the corpus was already
    standing.  There is no third case, so there is no NOT_DATED sentinel here:
    a control either has a dated application or it is pre-existing.
    """
    for row in rows:
        value = (row["applied_utc"] or "").strip()
        if value == PRE_EXISTING:
            continue
        if parse_utc(value) is None:
            raise ValueError(
                f"row {row['id']}: applied_utc must be ISO-8601 UTC or PRE_EXISTING, got {value!r}"
            )


def load_rows(path: Path = CLOCK_CSV) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{path} has no header row")
        fieldnames, rows = list(reader.fieldnames), list(reader)
    validate_applied_utc(rows)
    return fieldnames, rows


def compute(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return rows with p_wall_hours / p_wall_hhmm filled in where defined.

    Rows are copied; the input is not modified.
    """
    computed: list[dict[str, str]] = []
    for row in rows:
        out = dict(row)
        reason = reason_not_computed(row)
        if reason is None:
            applied = parse_utc(row["applied_utc"])
            reconstituted = parse_utc(row["reconstituted_utc"])
            assert applied is not None and reconstituted is not None  # reason_not_computed checked
            if reconstituted < applied:
                raise ValueError(
                    f"row {row['id']}: reconstituted_utc precedes applied_utc "
                    f"({row['reconstituted_utc']} < {row['applied_utc']})"
                )
            interval = compute_interval(applied, reconstituted)
            out["p_wall_hours"] = f"{interval.hours:.4f}"
            out["p_wall_hhmm"] = interval.hhmm
        else:
            out["p_wall_hours"] = ""
            out["p_wall_hhmm"] = ""
            out["notes"] = append_note(out.get("notes", ""), f"No P_wall: {reason}.")
        computed.append(out)
    return computed


def write_output(fieldnames: list[str], rows: list[dict[str, str]], path: Path = OUTPUT_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out_fields = list(fieldnames) + [c for c in COMPUTED_COLUMNS if c not in fieldnames]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(rows)


def summarise(rows: list[dict[str, str]]) -> str:
    """Console summary by row type and state."""
    lines: list[str] = []
    lines.append("Protection time - computed from data/clock.csv")
    lines.append("=" * 72)
    lines.append("")

    order = ["A_applied_nested", "B_applied_nonnested", "C_standing", "X_out_of_corpus"]
    titles = {
        "A_applied_nested": "Type A - applied during the incident, nested intervals",
        "B_applied_nonnested": "Type B - applied during the incident, not nested",
        "C_standing": "Type C - pre-existing controls (no P_wall by definition)",
        "X_out_of_corpus": "Type X - outside the corpus (rule check)",
    }

    for row_type in order:
        group = [r for r in rows if r["row_type"] == row_type]
        if not group:
            lines.append(titles[row_type])
            lines.append("-" * 72)
            lines.append("  (no rows: the schema keeps this type defined, the corpus contains none)")
            lines.append("")
            continue
        lines.append(titles[row_type])
        lines.append("-" * 72)
        for row in group:
            p_wall = row["p_wall_hhmm"] or "-"
            lines.append(f"  {row['id']:<3}  {row['state']:<20}  P_wall = {p_wall:<16}  {row['control'][:60]}")
        lines.append("")

    lines.append("States by row type")
    lines.append("-" * 72)
    states = sorted({r["state"] for r in rows})
    header = f"  {'row type':<22}" + "".join(f"{s[:18]:>20}" for s in states)
    lines.append(header)
    for row_type in order:
        group = [r for r in rows if r["row_type"] == row_type]
        if not group:
            continue
        counts = "".join(f"{sum(1 for r in group if r['state'] == s):>20}" for s in states)
        lines.append(f"  {row_type:<22}{counts}")
    lines.append("")

    computed_rows = [r for r in rows if r["p_wall_hours"]]
    lines.append(f"Rows total: {len(rows)}   with P_wall: {len(computed_rows)}   without: {len(rows) - len(computed_rows)}")
    standing = [r for r in rows if r["row_type"] == "C_standing"]
    lines.append(
        f"Type C rows: {len(standing)}, of which with a P_wall value: "
        f"{sum(1 for r in standing if r['p_wall_hours'])} (must be 0)"
    )
    lines.append("")
    lines.append("The corpus contains exactly one control-application event: the Artifactory rebuild")
    lines.append("of 2026-07-06T01:16Z. Every other control in the corpus was already standing.")
    lines.append("")
    lines.append("P_wall is calendar time. P_exp (agent exposure time) is not computed here:")
    lines.append("no public data exists on when evaluation workloads ran. See src/sensitivity.py.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clock", type=Path, default=CLOCK_CSV, help="path to clock.csv")
    parser.add_argument("--out", type=Path, default=OUTPUT_CSV, help="path to the output CSV")
    parser.add_argument("--quiet", action="store_true", help="write the file without the summary")
    args = parser.parse_args(argv)

    fieldnames, rows = load_rows(args.clock)
    computed = compute(rows)
    write_output(fieldnames, computed, args.out)
    if not args.quiet:
        print(summarise(computed))
        print()
        print(f"Written: {args.out.relative_to(REPO_ROOT) if args.out.is_relative_to(REPO_ROOT) else args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
