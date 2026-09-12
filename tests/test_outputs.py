"""The generated artefacts: figures and paper tables.

These check that the generators run and that what they emit still says what the
evidence base says. They are cheap; the expensive rendering is behind a marker
so the fast suite stays fast.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))


def test_paper_tables_are_generated_not_written() -> None:
    import paper_tables

    text = paper_tables.build()
    assert "Generated file — do not edit by hand" in text
    for heading in ("Table 1", "Table 2", "Table 3", "Table 4", "Table 5"):
        assert f"## {heading}" in text, heading


def test_paper_tables_carry_the_three_reference_values() -> None:
    import paper_tables

    text = paper_tables.build()
    for value in ("46 h 50 min", "62 h 45 min", "175 h 30 min"):
        assert value in text, value


def test_paper_tables_carry_the_load_bearing_caveats() -> None:
    """A table pasted into a paper must not shed the qualifications around it."""
    import paper_tables

    text = paper_tables.build()
    # The (d) scope caveat, elevated above the table rather than trailing it.
    assert "What 'breached' means here" in text
    assert "different quantity" in text
    # The asynchronous-review precision point.
    assert "asynchronous review to blocking intervention, not the interval" in text
    # C8's state flag.
    assert "not determinable from the source" in text
    # The unresolved interpretive question.
    assert "The ambiguity is the finding" in text


def test_paper_tables_mark_uncounted_instrument_cells() -> None:
    import paper_tables

    text = paper_tables.build()
    assert "it is not a zero" in text


def test_no_bare_p_in_generated_prose() -> None:
    """The writing rule: always P_wall or P_exp, never a bare P."""
    import re

    import paper_tables

    text = paper_tables.build()
    # A bare capital P as a standalone token, not followed by _wall / _exp,
    # and not part of a source code (P1, P19) or a word.
    offenders = re.findall(r"(?<![\w`_])P(?![\w_])(?!_)", text)
    assert not offenders, f"{len(offenders)} bare 'P' occurrences in the generated tables"


def test_figures_module_imports_without_rendering() -> None:
    import figures

    assert len(figures.SERIES) >= 5
    assert figures.STATE_ORDER


@pytest.mark.slow
def test_all_four_figures_render_to_png_and_pdf(tmp_path: Path) -> None:
    import figures

    figures.apply_print_style()
    rows = figures.load_rows()
    written = (
        figures.figure_1(rows) + figures.figure_2(rows)
        + figures.figure_3(rows) + figures.figure_4()
    )
    assert len(written) == 8
    for path in written:
        assert path.exists() and path.stat().st_size > 1000, path
    suffixes = {p.suffix for p in written}
    assert suffixes == {".png", ".pdf"}


# --- the documents a reviewer is pointed at --------------------------------

REQUIRED_README_ANCHORS = [
    # The four findings that live only in the repository.
    "exactly one control-application event",
    "B1` and `B2",
    "no measurable `P_wall`",
    "Nineteen research errors",
    # Reproduction and navigation.
    "./verify.sh",
    "46 h 50 min",
    "docs/limitations.md",
    "docs/methodology.md",
    "docs/belegbasis-v3.md",
    # Dual use.
    "no exploit code",
    "mechanism inventory",
]

REQUIRED_LIMITATIONS_ANCHORS = [
    "none for its magnitude",              # P_exp: ordering proved, magnitude not
    "One incident",
    "spoofed tool calls",
    "Type-C rows carry no `P`",
    "not determinable from the source",
    "qualitative reading, not a term count",
    "not to regulatory filing",
    "What would change the result",
]


def test_readme_carries_its_required_anchors() -> None:
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    missing = [a for a in REQUIRED_README_ANCHORS if a not in text]
    assert not missing, f"README.md is missing: {missing}"


def test_readme_stays_navigational() -> None:
    """The README answers 'what is in here and how do I check it', not the paper's argument."""
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert len(text.splitlines()) < 200, "README has grown into a second paper"


def test_limitations_document_carries_every_required_limitation() -> None:
    text = (REPO_ROOT / "docs" / "limitations.md").read_text(encoding="utf-8")
    missing = [a for a in REQUIRED_LIMITATIONS_ANCHORS if a not in text]
    assert not missing, f"docs/limitations.md is missing: {missing}"


def test_limitations_names_the_seven_percent_figure() -> None:
    """The sharpest limitation must carry its number, not a euphemism."""
    text = (REPO_ROOT / "docs" / "limitations.md").read_text(encoding="utf-8")
    assert "7%" in text
    assert "96 transcripts" in text
    assert "W-4" in text


def test_writing_rule_holds_in_the_documents() -> None:
    """Always P_wall or P_exp, never a bare P."""
    import re

    for name in ("README.md", "docs/limitations.md", "docs/methodology.md"):
        text = (REPO_ROOT / name).read_text(encoding="utf-8")
        # Strip inline code and fenced blocks, where `P` is quoted as notation.
        stripped = re.sub(r"```.*?```", "", text, flags=re.S)
        stripped = re.sub(r"`[^`]*`", "", stripped)
        offenders = re.findall(r"(?<![\w_])P(?![\w_])", stripped)
        assert not offenders, f"{name}: {len(offenders)} bare 'P' occurrence(s)"
