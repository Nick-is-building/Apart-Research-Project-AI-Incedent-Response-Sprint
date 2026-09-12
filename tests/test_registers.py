"""Cross-checks over the three data registers.

data/sources.csv is the single place a source code resolves to a URL and a
date. These tests make it impossible for a row in clock.csv, contradictions.csv
or instruments.csv to cite a code that is not registered there.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

DATA = REPO_ROOT / "data"

# A source code: P1, P19, N2, N10, S01, X01, CV1. Optionally followed by a
# locator (P1-X, P1-IX.A). Deliberately anchored so that ordinary prose words
# are not mistaken for codes.
CODE = re.compile(r"\b(P\d{1,2}|N\d{1,2}|S\d{2}|X\d{2}|CV\d)\b")

# Prose that legitimately appears in provenance fields without being a code.
NON_CODE_PREFIXES = ("evidence base", "collusion.wiki")


def read(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def registered_codes() -> set[str]:
    return {row["key"] for row in read("sources.csv")}


def cited_codes(text: str) -> set[str]:
    return set(CODE.findall(text or ""))


# --- task 1: sources.csv exists and covers everything that cites it ---------

def test_sources_register_exists_and_is_populated(registered_codes: set[str]) -> None:
    assert len(registered_codes) >= 50


def test_every_source_has_a_code_and_a_date() -> None:
    for row in read("sources.csv"):
        assert row["key"].strip(), row
        assert row["date"].strip(), f"{row['key']}: no date"
        assert row["title"].strip(), f"{row['key']}: no title"


def test_every_source_has_a_url_or_says_why_not() -> None:
    """A missing URL is allowed only where the evidence base records none."""
    for row in read("sources.csv"):
        if row["url"].strip():
            assert row["url"].startswith(("http://", "https://")) or "." in row["url"], row["key"]
        else:
            assert row["notes"].strip(), (
                f"{row['key']}: no URL and no note explaining why"
            )


@pytest.mark.parametrize(
    ("filename", "columns"),
    [
        ("clock.csv", ("provenance", "goal_source_ref")),
        ("contradictions.csv", ("source_a", "source_b")),
        ("instruments.csv", ("source_ref",)),
    ],
)
def test_cited_codes_resolve_to_the_register(
    registered_codes: set[str], filename: str, columns: tuple[str, ...]
) -> None:
    unknown: dict[str, set[str]] = {}
    for row in read(filename):
        row_id = row[next(iter(row))]
        for column in columns:
            missing = cited_codes(row[column]) - registered_codes
            if missing:
                unknown.setdefault(row_id, set()).update(missing)
    assert not unknown, f"{filename} cites codes absent from sources.csv: {unknown}"


@pytest.mark.parametrize(
    ("filename", "column"),
    [("clock.csv", "provenance"), ("contradictions.csv", "source_a"), ("instruments.csv", "source_ref")],
)
def test_every_row_cites_at_least_one_registered_source(
    registered_codes: set[str], filename: str, column: str
) -> None:
    for row in read(filename):
        row_id = row[next(iter(row))]
        value = row[column]
        has_code = bool(cited_codes(value) & registered_codes)
        has_prose = any(value.lower().startswith(p) for p in NON_CODE_PREFIXES)
        assert has_code or has_prose, f"{filename} row {row_id}: {column} cites nothing"


# --- task 2: the instruments register --------------------------------------

def test_no_instrument_has_a_time_axis() -> None:
    """The project's novelty claim, as a regression test.

    If any instrument ever gains a time axis for containment, this fails and
    the claim has to be rewritten rather than quietly carried forward.
    """
    offenders = [r["id"] for r in read("instruments.csv") if r["n_time_axis_present"] != "FALSE"]
    assert offenders == [], f"instruments with a time axis: {offenders}"


def test_instrument_counts_are_integers_or_deliberately_blank() -> None:
    """A blank count means the evidence base gives none. It is not a zero."""
    count_columns = [
        "n_duration", "n_how_long", "n_withstand", "n_containment",
        "n_egress", "n_hours", "n_minutes",
    ]
    for row in read("instruments.csv"):
        for column in count_columns:
            value = row[column].strip()
            if value:
                assert value.isdigit(), f"{row['id']}.{column} = {value!r}"


def test_count_method_is_recorded_for_every_instrument() -> None:
    """Never assume a full-text scan where the evidence base does not say so."""
    permitted = {
        "full_text_term_count",
        "full_text_term_count_aggregated_over_cluster",
        "partial_read_full_term_search",
        "term_search_only",
        "qualitative_no_term_count",
    }
    for row in read("instruments.csv"):
        assert row["count_method"] in permitted, f"{row['id']}: {row['count_method']!r}"


def test_instruments_without_a_term_count_carry_no_numbers() -> None:
    """A qualitative row must not look like a counted one."""
    count_columns = [
        "n_duration", "n_how_long", "n_withstand", "n_containment",
        "n_egress", "n_hours", "n_minutes",
    ]
    for row in read("instruments.csv"):
        if row["count_method"] == "qualitative_no_term_count":
            assert all(not row[c].strip() for c in count_columns), row["id"]


def test_instrument_ids_are_unique_and_ordered() -> None:
    ids = [row["id"] for row in read("instruments.csv")]
    assert len(ids) == len(set(ids))
    assert ids == sorted(ids)


# --- task 5: the contradiction register ------------------------------------

def test_contradiction_register_has_w1_to_w9() -> None:
    ids = [row["id"] for row in read("contradictions.csv")]
    assert ids == [f"W-{n}" for n in range(1, 10)]


def test_exactly_four_contradictions_go_to_the_main_text() -> None:
    main = {row["id"] for row in read("contradictions.csv") if row["in_paper_main_text"] == "TRUE"}
    assert main == {"W-1", "W-2", "W-8", "W-9"}


def test_contradiction_booleans_and_status() -> None:
    for row in read("contradictions.csv"):
        assert row["intra_document"] in {"TRUE", "FALSE"}, row["id"]
        assert row["in_paper_main_text"] in {"TRUE", "FALSE"}, row["id"]
        assert row["status"] == "PRIMARY_CONFLICT", row["id"]


def test_every_contradiction_has_both_claims_and_a_question() -> None:
    for row in read("contradictions.csv"):
        for column in ("claim_a", "claim_b", "resolving_question", "short_title"):
            assert row[column].strip(), f"{row['id']}: empty {column}"


def test_intra_document_rows_name_the_same_document() -> None:
    """An intra-document contradiction must cite the same source on both sides."""
    for row in read("contradictions.csv"):
        if row["intra_document"] != "TRUE":
            continue
        codes_a = cited_codes(row["source_a"])
        codes_b = cited_codes(row["source_b"])
        assert codes_a & codes_b, (
            f"{row['id']} is marked intra-document but cites {codes_a} against {codes_b}"
        )
