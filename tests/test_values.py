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
    "unclassified",  # reconstitution happened, the sources do not say how
    "none",  # no reconstitution occurred
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


def test_all_type_a_rows_are_bypassed(rows: list[dict[str, str]]) -> None:
    """state describes the control applied at t0, not the surrounding system.

    None of the three type-A controls was itself overcome: each capability came
    back by a route the t0 measure did not block.
    """
    type_a = [r for r in rows if r["row_type"] == "A_applied_nested"]
    assert {r["state"] for r in type_a} == {"bypassed"}


def test_unclassified_is_only_used_where_reconstitution_happened(rows: list[dict[str, str]]) -> None:
    """'unclassified' means the how is unknown; 'none' means it did not happen."""
    for row in rows:
        if row["reconstitution_category"] == "unclassified":
            assert row["reconstituted_utc"] != "NEVER", row["id"]
        if row["reconstitution_category"] == "none":
            assert row["reconstituted_utc"] in {"NEVER", "NOT_DATED"}, row["id"]


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


def test_no_id_contradicts_its_row_type(rows: list[dict[str, str]]) -> None:
    """A cold reader must not meet id B1 sitting under row_type C_standing."""
    prefix_for = {
        "A_applied_nested": "A",
        "B_applied_nonnested": "B",
        "C_standing": "C",
        "X_out_of_corpus": "X",
    }
    for row in rows:
        assert row["id"].startswith(prefix_for[row["row_type"]]), (
            f"{row['id']} has row_type {row['row_type']}"
        )


def test_type_b_is_defined_but_empty(rows: list[dict[str, str]]) -> None:
    """The corpus contains no applied, non-nested control.

    The type stays in the schema because the distinction is real; it is empty
    because every control in the corpus other than the 6 July rebuild was
    already standing.
    """
    assert [r["id"] for r in rows if r["row_type"] == "B_applied_nonnested"] == []


def test_exactly_one_control_application_event(rows: list[dict[str, str]]) -> None:
    """Every row is either the 6 July rebuild or a pre-existing control."""
    applied = {r["applied_utc"] for r in rows}
    assert applied == {"2026-07-06T01:16Z", "PRE_EXISTING"}, applied


def test_applied_utc_has_no_not_dated_sentinel(rows: list[dict[str, str]]) -> None:
    for row in rows:
        assert row["applied_utc"] != "NOT_DATED", row["id"]


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


# --- the nesting argument in src/sensitivity.py ----------------------------

def test_sensitivity_loads_exactly_three_type_a_rows() -> None:
    import sensitivity

    assert len(sensitivity.load_type_a()) == 3


def test_sensitivity_verifies_nesting() -> None:
    import sensitivity

    nested, _ = sensitivity.verify_nesting(sensitivity.load_type_a())
    assert nested


def test_monte_carlo_ordering_holds_in_every_draw() -> None:
    """The proof says 100%. A smaller run, so the suite stays fast."""
    import sensitivity

    rows = sensitivity.load_type_a()
    _, violations, _, _ = sensitivity.monte_carlo(rows, draws=1_200, grid_points=1_500)
    assert violations == 0


def test_cumulative_exposure_is_monotone_for_every_family() -> None:
    """Monotone by construction: this is what makes the 100% exact, not lucky."""
    import numpy as np

    import sensitivity

    rng = np.random.default_rng(7)
    rows = sensitivity.load_type_a()
    grid = sensitivity.build_grid([r.p_wall_hours for r in rows], 1_500)
    for family in sensitivity.DUTY_CYCLE_FAMILIES:
        for _ in range(25):
            duty = sensitivity.draw_duty_cycle(family, grid, rng)
            assert (duty >= 0).all(), family
            cumulative = sensitivity.cumulative_exposure(grid, duty)
            assert np.all(np.diff(cumulative) >= 0), family


def test_alpha_reversal_threshold_matches_the_evidence_base() -> None:
    """Evidence base 18.1, limitation 3: reversal at alpha_A3 < 0.2669 * alpha_A1."""
    import sensitivity

    rows = sensitivity.load_type_a()
    threshold = rows[0].p_wall_hours / rows[2].p_wall_hours
    assert round(threshold, 4) == 0.2669


# --- state_determinable ------------------------------------------------------

def test_state_determinable_is_boolean(rows: list[dict[str, str]]) -> None:
    for row in rows:
        assert row["state_determinable"] in {"TRUE", "FALSE"}, row["id"]


def test_exactly_one_state_is_not_source_determinable(rows: list[dict[str, str]]) -> None:
    """C8 is the only row whose state cannot be settled from the evidence.

    P1 records that the first host-mount pod failed and a second succeeded
    minutes later, without describing how they differed. 'broken' is recorded,
    but it is a claim, not a reading of the source.
    """
    undeterminable = [r["id"] for r in rows if r["state_determinable"] == "FALSE"]
    assert undeterminable == ["C8"], undeterminable


def test_undeterminable_states_say_so_in_notes(rows: list[dict[str, str]]) -> None:
    for row in rows:
        if row["state_determinable"] == "FALSE":
            assert "cannot be made from the source" in row["notes"], row["id"]


# --- src/budgets.py: the four calculations ----------------------------------

def test_budget_measured_response_is_334_minutes() -> None:
    """Evidence base 16.3a: alert 12:03, runs stopped 17:37."""
    import budgets

    measured = budgets.minutes_between(budgets.OPENAI_ALERT, budgets.OPENAI_RUNS_STOPPED)
    assert measured == 334
    assert budgets.hhmm(measured) == "5 h 34 min"


def test_budget_factors_match_the_evidence_base() -> None:
    """Evidence base 16.3a: 11.1x against 30 minutes, 5.6x against 60."""
    import budgets

    measured = budgets.minutes_between(budgets.OPENAI_ALERT, budgets.OPENAI_RUNS_STOPPED)
    assert round(measured / budgets.FALSE_POSITIVE_WINDOW_MIN, 1) == 11.1
    assert round(measured / budgets.FULL_CHAIN_MIN, 1) == 5.6


def test_aisi_latencies_match_the_evidence_base() -> None:
    """Evidence base 16.3a: 46 minutes reaction, 11 h 41 min detection."""
    import budgets

    detection = budgets.minutes_between(budgets.AISI_ACTIVITY_ENDED, budgets.AISI_ALERT)
    reaction = budgets.minutes_between(budgets.AISI_ALERT, budgets.AISI_EVALS_TERMINATED)
    assert reaction == 46
    assert budgets.hhmm(detection) == "11 h 41 min"


def test_cadence_ratios_land_between_50_and_187() -> None:
    """Evidence base 12.5: one year against the measured hold times."""
    import budgets

    type_a = budgets.load_type_a_p_wall()
    ratios = sorted(budgets.HOURS_PER_YEAR / p_wall for _, _, p_wall in type_a)
    assert round(ratios[0]) == 50
    assert round(ratios[-1]) == 187


def test_awareness_clock_reproduces_the_evidence_base_table() -> None:
    """Evidence base 16.2: 1 day, 2-3 days, 12 days, 16 days."""
    import budgets

    labels = [r.days_label(budgets.DISCLOSURE) for r in budgets.AWARENESS_READINGS]
    assert labels == ["1", "2-3", "12", "16"]


def test_awareness_clock_verdicts() -> None:
    """Two readings breach the EU clock; the 5 July reading also breaches California by one day."""
    import budgets

    eu = [budgets.verdict(r, budgets.DISCLOSURE, budgets.EU_CYBER_DEADLINE_DAYS)
          for r in budgets.AWARENESS_READINGS]
    ca = [budgets.verdict(r, budgets.DISCLOSURE, budgets.CAL_DEADLINE_DAYS)
          for r in budgets.AWARENESS_READINGS]

    assert eu == ["met", "met", "BREACHED by 7 d", "BREACHED by 11 d"]
    assert ca == ["met", "met", "met", "BREACHED by 1 d"]


def test_a_range_that_straddles_a_deadline_is_not_decided() -> None:
    """A reading given as a range must not be silently collapsed to one verdict."""
    import datetime

    import budgets

    straddling = budgets.AwarenessReading(
        "hypothetical", datetime.date(2026, 7, 15), "-", "PRIMARY",
        awareness_latest=datetime.date(2026, 7, 17),
    )
    assert budgets.verdict(straddling, budgets.DISCLOSURE, 5) == "depends on reading"


def test_budget_report_carries_the_asynchronous_precision_point() -> None:
    """The 30-minute figure predates the August commitment; that must print."""
    import budgets

    report = budgets.build_report()
    assert "ASYNCHRONOUS REVIEW to BLOCKING INTERVENTION" in report
    assert "19 March 2026" in report
    assert "overstates it" in report


def test_budget_report_carries_the_unresolved_interpretive_question() -> None:
    import budgets

    report = budgets.build_report()
    assert "The ambiguity is the finding" in report
    assert "This repository does not pick one" in report


# --- out-of-corpus rows are checks on the rule, never measurements ----------

def test_out_of_corpus_rows_carry_no_p_wall(rows: list[dict[str, str]]) -> None:
    """Three X rows from three incidents are not three measurements.

    Every out-of-corpus row is a pre-existing standing control, so none has an
    application event and none can carry a P_wall. A reviewer must not be able
    to read the X block as widening the measured corpus.
    """
    out_of_corpus = [r for r in rows if r["row_type"] == "X_out_of_corpus"]
    assert len(out_of_corpus) >= 3
    for row in out_of_corpus:
        assert row["applied_utc"] == "PRE_EXISTING", row["id"]
        assert not row["p_wall_hours"] and not row["p_wall_hhmm"], row["id"]


def test_only_type_a_rows_are_measured(rows: list[dict[str, str]]) -> None:
    """The measured corpus is exactly the three rows from the 6 July rebuild."""
    measured = sorted(r["id"] for r in rows if r["p_wall_hours"])
    assert measured == ["A1", "A2", "A3"], measured


def test_x3_separates_operator_statement_from_reporting(by_id: dict[str, dict[str, str]]) -> None:
    """The causal clause was never part of the operator statement.

    Reporting supplied "because they were not supposed to have web access";
    OpenAI supplied the route. The row must keep those apart, and must not
    quote wording that is only known through reporting.
    """
    row = by_id["X3"]
    notes = row["notes"]
    assert "used the RubyGems platform to reach the internet" in notes
    assert "Reporting adds, and OpenAI does not" in notes
    assert "is not part of the operator statement" in notes
    assert "makeshift browser" not in notes, "wording known only through reporting"
    assert row["status"] == "SECONDARY"
    assert row["goal_source"] == "operator_stated"
