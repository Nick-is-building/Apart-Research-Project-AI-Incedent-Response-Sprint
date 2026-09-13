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


# --- the submission template record ----------------------------------------

def test_paper_template_records_the_requirements_verbatim() -> None:
    text = (REPO_ROOT / "docs" / "paper-template.md").read_text(encoding="utf-8")
    for anchor in (
        "150 words or fewer",
        "Limitations and Dual-Use / Ethical appendix",
        "Research report (PDF) using the official template",
        "3 to 5 minute video demo",
        "not a product demo",
    ):
        assert anchor in text, anchor


def test_paper_template_records_the_template_not_a_reconstruction() -> None:
    """The structure is now read from the file; the pending guard has retired.

    The recorded page setup must match the template's own sectPr, so a later
    edit cannot substitute plausible values for measured ones.
    """
    import zipfile
    import xml.etree.ElementTree as ET

    text = (REPO_ROOT / "docs" / "paper-template.md").read_text(encoding="utf-8")
    template = REPO_ROOT / "Digital Minds Research Sprint submission template.docx"
    with zipfile.ZipFile(template) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    page = document.find(".//w:sectPr/w:pgSz", ns)
    width = page.get("{%s}w" % ns["w"])
    assert width in text, f"recorded page width does not match the template ({width})"



# --- the assembled paper ----------------------------------------------------

def test_every_generation_marker_is_filled() -> None:
    """No [Claude Code: ...] marker may survive into the assembled paper."""
    import assemble_paper

    text, filled, placed = assemble_paper.build()
    assert len(filled) == 6, filled
    assert not assemble_paper.MARKER.search(text)


def test_abstract_is_exactly_149_words_and_unedited() -> None:
    import assemble_paper

    text, _, _ = assemble_paper.build()
    abstract = text[text.index("## Abstract"):text.index("## 1. Introduction")]
    body = abstract.split("---")[0].replace("## Abstract", "").strip()
    assert len(body.split()) == 149

    source = (REPO_ROOT / "paper-text.md").read_text(encoding="utf-8")
    assert body in source, "the abstract was altered during assembly"


def test_all_four_figures_are_placed_where_the_text_supports_them() -> None:
    import assemble_paper

    text, _, placed = assemble_paper.build()
    assert len(placed) == 4
    assert "### 4.1 Three protection times, verified to the minute" in placed
    assert any(s.startswith("### 4.6") for s in placed)

    # Figure 1 with 4.1 and Figure 4 with 4.6, as specified.
    for figure, section in (("**Figure 1.**", "### 4.1"), ("**Figure 4.**", "### 4.6")):
        heading = text.rindex(section, 0, text.index(figure))
        between = text[heading:text.index(figure)]
        assert "\n### " not in between[len(section):], f"{figure} drifted out of {section}"


def test_paper_prose_is_copied_through_unchanged() -> None:
    """The assembler fills markers and places figures. It does not rewrite prose."""
    import assemble_paper

    text, _, _ = assemble_paper.build()
    source = (REPO_ROOT / "paper-text.md").read_text(encoding="utf-8")
    for paragraph in (
        "All three controls were bypassed; none was broken",
        "The apparatus is built around the model as an asset to protect, not as an actor to bound.",
        "This is n = 1.",
    ):
        assert paragraph in source and paragraph in text, paragraph


def test_paper_carries_no_bare_p() -> None:
    import re

    import assemble_paper

    text, _, _ = assemble_paper.build()
    stripped = re.sub(r"```.*?```", "", text, flags=re.S)
    stripped = re.sub(r"`[^`]*`", "", stripped)
    stripped = re.sub(r"\bP\d+\b", "", stripped)
    offenders = re.findall(r"(?<![\w_])P(?![\w_])", stripped)
    assert not offenders, f"{len(offenders)} bare 'P' occurrence(s) in the paper"


def test_claims_check_reports_rather_than_reconciles() -> None:
    """Claims that disagree with the data must be surfaced, not quietly fixed."""
    import check_claims

    claims = check_claims.collect()
    assert len(claims) >= 50
    failing = [c for c in claims if c.status != check_claims.OK]
    # Every claim should now reproduce; any that does not must carry a note
    # explaining the disagreement rather than being quietly reconciled.
    for c in failing:
        assert c.note, f"{c.claim}: a non-reproducing claim must carry a note"
    assert not failing, [c.claim for c in failing]
