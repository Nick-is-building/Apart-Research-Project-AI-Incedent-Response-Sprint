"""Regression tests against the target values stated in the evidence base.

The three type-A target values come from docs/belegbasis-v3.md section 4.3.
If any of them moves, the arithmetic or the data is wrong and nothing further
in the repository should be trusted until it is resolved.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

import compute_p  # noqa: E402

VALID_ROW_TYPES = {
    "A_applied_nested",
    "B_applied_nonnested",
    "C_standing",
    "X_out_of_corpus",
}
VALID_STATES = {"broken", "bypassed", "fired_not_escalated", "held", "defeated_no_effect"}
VALID_CATEGORIES = {
    "K1_alternative",
    "K2_training",
    "K3_residue",
    "K4_escalation",
    "K5_ephemeral",
    "none",
}
VALID_STATUSES = {
    "PRIMARY",
    "PRIMARY_CONFLICT",
    "SECONDARY",
    "OWN_RECONSTRUCTION",
    "UNVERIFIED",
    "REFUTED",
}

# Evidence base 4.3. Minutes, so the comparison is exact rather than float-fuzzy.
TARGET_VALUES = {
    "A1": (46 * 60 + 50, "46 h 50 min", 46.8333),
    "A2": (62 * 60 + 45, "62 h 45 min", 62.75),
    "A3": (175 * 60 + 30, "175 h 30 min", 175.5),
}


@pytest.fixture(scope="module")
def rows() -> list[dict[str, str]]:
    _, raw = compute_p.load_rows()
    return compute_p.compute(raw)


@pytest.fixture(scope="module")
def by_id(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["id"]: row for row in rows}


# --- the three target values ------------------------------------------------

@pytest.mark.parametrize("row_id", sorted(TARGET_VALUES))
def test_type_a_target_values(by_id: dict[str, dict[str, str]], row_id: str) -> None:
    expected_minutes, expected_hhmm, expected_hours = TARGET_VALUES[row_id]
    row = by_id[row_id]

    assert row["p_wall_hhmm"] == expected_hhmm
    assert float(row["p_wall_hours"]) == pytest.approx(expected_hours, abs=5e-5)

    applied = compute_p.parse_utc(row["applied_utc"])
    reconstituted = compute_p.parse_utc(row["reconstituted_utc"])
    assert applied is not None and reconstituted is not None
    actual_minutes = int((reconstituted - applied).total_seconds() // 60)
    assert actual_minutes == expected_minutes


# --- the rule that must not be broken --------------------------------------

def test_no_type_c_row_has_a_p_wall(rows: list[dict[str, str]]) -> None:
    """Type C rows are pre-existing controls: no application event, no P_wall."""
    offenders = [
        r["id"] for r in rows if r["row_type"] == "C_standing" and (r["p_wall_hours"] or r["p_wall_hhmm"])
    ]
    assert offenders == [], f"type C rows must not carry a P_wall: {offenders}"


def test_every_type_c_row_is_pre_existing(rows: list[dict[str, str]]) -> None:
    for row in rows:
        if row["row_type"] == "C_standing":
            assert row["applied_utc"] == "PRE_EXISTING", row["id"]


# --- provenance and status discipline --------------------------------------

def test_every_row_has_provenance_and_status(rows: list[dict[str, str]]) -> None:
    for row in rows:
        assert row["provenance"].strip(), f"{row['id']}: empty provenance"
        assert row["status"].strip(), f"{row['id']}: empty status"
        assert row["status"] in VALID_STATUSES, f"{row['id']}: unknown status {row['status']!r}"


def test_project_assumption_has_no_goal_source_ref(rows: list[dict[str, str]]) -> None:
    for row in rows:
        if row["goal_source"] == "project_assumption":
            assert row["goal_source_ref"].strip() == "", (
                f"{row['id']}: project_assumption must leave goal_source_ref empty"
            )


def test_operator_stated_has_a_goal_source_ref(rows: list[dict[str, str]]) -> None:
    for row in rows:
        if row["goal_source"] == "operator_stated":
            assert row["goal_source_ref"].strip(), f"{row['id']}: operator_stated needs a reference"


def test_enums(rows: list[dict[str, str]]) -> None:
    for row in rows:
        assert row["row_type"] in VALID_ROW_TYPES, row["id"]
        assert row["state"] in VALID_STATES, row["id"]
        assert row["reconstitution_category"] in VALID_CATEGORIES, row["id"]
        assert row["goal_source"] in {"operator_stated", "project_assumption"}, row["id"]


def test_ids_are_unique(rows: list[dict[str, str]]) -> None:
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids))


def test_no_invented_timestamps(rows: list[dict[str, str]]) -> None:
    """Every timestamp field is either a sentinel, empty, or valid ISO-8601 UTC."""
    for row in rows:
        for column in ("applied_utc", "held_evidence_utc", "reconstituted_utc"):
            value = row[column].strip()
            if value in compute_p.SENTINELS:
                continue
            assert compute_p.parse_utc(value) is not None, f"{row['id']}.{column} = {value!r}"


# --- the nesting the sensitivity argument rests on -------------------------

def test_type_a_rows_are_nested(rows: list[dict[str, str]]) -> None:
    """Same start, strictly ascending end points: [t0,A1] subset [t0,A2] subset [t0,A3]."""
    type_a = [r for r in rows if r["row_type"] == "A_applied_nested"]
    assert len(type_a) == 3

    starts = {r["applied_utc"] for r in type_a}
    assert starts == {"2026-07-06T01:16Z"}, f"type A rows must share one applied_utc, got {starts}"

    ends = [compute_p.parse_utc(r["reconstituted_utc"]) for r in sorted(type_a, key=lambda r: r["id"])]
    assert all(e is not None for e in ends)
    assert ends[0] < ends[1] < ends[2]


def test_type_b_breaks_the_nesting(by_id: dict[str, dict[str, str]]) -> None:
    """Type B rows do not share the type-A start, which is why they are kept apart."""
    for row_id in ("B1", "B2"):
        assert by_id[row_id]["applied_utc"] != "2026-07-06T01:16Z"


# --- held evidence must sit inside the interval ----------------------------

def test_held_evidence_lies_within_the_interval(rows: list[dict[str, str]]) -> None:
    for row in rows:
        held = compute_p.parse_utc(row["held_evidence_utc"])
        applied = compute_p.parse_utc(row["applied_utc"])
        reconstituted = compute_p.parse_utc(row["reconstituted_utc"])
        if held is None or applied is None:
            continue
        assert applied <= held, f"{row['id']}: held evidence precedes application"
        if reconstituted is not None:
            assert held <= reconstituted, f"{row['id']}: held evidence follows reconstitution"
