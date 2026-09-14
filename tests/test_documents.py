"""Load-bearing warnings and constraints in the prose documents.

These exist because the qualifications are the part most likely to be lost in
a later edit: they are the sentences that stop a claim being overstated, and
nothing else in the repository would notice if they disappeared.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

EVIDENCE_BASE = REPO_ROOT / "docs" / "belegbasis-v3.md"
CLAUSE = REPO_ROOT / "docs" / "clause-ais-13-m.md"


@pytest.fixture(scope="module")
def evidence_base() -> str:
    return EVIDENCE_BASE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def clause() -> str:
    return CLAUSE.read_text(encoding="utf-8")


# --- evidence base 15.7: three status markers that must survive verbatim ----

def test_section_15_7_is_no_longer_a_placeholder(evidence_base: str) -> None:
    assert "### 15.7" in evidence_base
    assert "PLATZHALTER" not in evidence_base


def test_p24_status_split_survives(evidence_base: str) -> None:
    """P24 is PRIMARY for the quoted passage only, SECONDARY for the rest.

    Collapsing this to 'primary' would credit press reporting to Amodei's own
    text.
    """
    assert "Status: PRIMÄR für die oben wörtlich zitierte Passage" in evidence_base
    assert "SEKUNDÄR für alle übrigen Angaben" in evidence_base


def test_p25_citation_warning_survives_unsoftened(evidence_base: str) -> None:
    """It is not established whether 'makeshift browser' is OpenAI's wording.

    The chain is OpenAI -> WSJ (quote or paraphrase, unknown) -> secondary
    reporting -> this document. The substance is undisputed; the wording is not
    attributable, and the paper must not present it as the affected party's
    phrasing.
    """
    assert "Zitierwarnung, verbindlich" in evidence_base
    assert "Im Paper nicht als Formulierung der betroffenen Partei ausgeben" in evidence_base
    assert "nicht belegt" in evidence_base
    assert "makeshift browser" in evidence_base


def test_dsewiki_attribution_warning_survives(evidence_base: str) -> None:
    """Usernames are not forensic evidence."""
    assert "Attributionswarnung zu DseWiki" in evidence_base
    assert "Ein Kontoname in einem offenen Wiki belegt forensisch nichts" in evidence_base
    assert "Kontonamen allenfalls als Illustration, nie als Beleg" in evidence_base


# --- the clause -------------------------------------------------------------

def test_clause_has_its_sections(clause: str) -> None:
    for heading in ("## 1.", "## 2.", "## 3.", "## 4.", "## 5.", "## 6.", "## 7."):
        assert heading in clause, heading


def test_clause_contains_no_bare_p(clause: str) -> None:
    """Always P_wall or P_exp, never a bare P.

    Source codes (P1, P19, P24) are excluded: they are identifiers, not the
    metric.
    """
    stripped = re.sub(r"```.*?```", "", clause, flags=re.S)
    stripped = re.sub(r"`[^`]*`", "", stripped)
    stripped = re.sub(r"\bP\d+\b", "", stripped)          # source codes
    offenders = re.findall(r"(?<![\w_])P(?![\w_])", stripped)
    assert not offenders, f"{len(offenders)} bare 'P' occurrence(s) in the clause"


def test_clause_cost_section_quantifies_nothing_beyond_the_published_figures(
    clause: str,
) -> None:
    """Section 6 may carry only the two figures traceable to OpenAI's statement.

    Those are roughly 20% of monitored inference compute, and a 30-minute alert
    target. Any other number in that section would be an invented cost estimate,
    which the section itself says it refuses to give.
    """
    start = clause.index("## 6. Cost")
    end = clause.index("## 7.")
    cost_section = clause[start:end]

    permitted = {"20", "30", "6", "13"}  # the two figures, plus section numbering
    found = set(re.findall(r"\d+(?:[.,]\d+)?", cost_section))
    unexpected = found - permitted
    assert not unexpected, f"unsourced numbers in the cost section: {sorted(unexpected)}"

    assert "20% of the inference compute being monitored" in cost_section
    assert "30 minutes" in cost_section
    assert "Any figure given here would be invented" in cost_section


def test_clause_keeps_its_scope_limits(clause: str) -> None:
    """The four 'what this does not do' claims are the honest half of the clause."""
    for anchor in (
        "It does not establish that an inventory is complete",
        "It does not prevent circumvention",
        "It does not replace monitoring",
        "It does not set a correct budget value",
        "Its audit is document-based",
    ):
        assert anchor in clause, anchor


# --- the mapping table resolves against the registers ----------------------

MAPPING_TO_REGISTERS = {
    # clause mapping row -> (instruments.csv ids, sources.csv codes)
    "CSA AICM AIS-13": (["I04"], ["N2"]),
    "CSA AICM AIS-11": (["I04"], ["N2"]),
    "NIST SP 800-53 SC-7(10)": (["I06"], ["N3"]),
    "NIST SP 800-53 SC-7": (["I06"], ["N3"]),
    "NIST SP 800-53 AU-9": (["I05"], ["N3"]),
    "EU AI Act, GPAI Code of Practice": (["I16", "I03"], ["N1"]),
    "California SB 53 §22757.15": ([], ["N9"]),
}


def read_csv(name: str) -> list[dict[str, str]]:
    with (REPO_ROOT / "data" / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_every_mapped_framework_resolves_to_the_registers(clause: str) -> None:
    """Nothing in the clause's mapping table may cite a framework we do not hold.

    California SB 53 maps to sources.csv only and deliberately carries no
    instrument row: it is a liability statute, not a control catalogue, so it
    was never term-counted for a containment time axis.
    """
    instrument_ids = {r["id"] for r in read_csv("instruments.csv")}
    source_codes = {r["key"] for r in read_csv("sources.csv")}

    unresolved: list[str] = []
    for framework, (instruments, sources) in MAPPING_TO_REGISTERS.items():
        assert framework in clause, f"mapping row missing from the clause: {framework}"
        for iid in instruments:
            if iid not in instrument_ids:
                unresolved.append(f"{framework} -> instruments.csv {iid}")
        for code in sources:
            if code not in source_codes:
                unresolved.append(f"{framework} -> sources.csv {code}")
    assert not unresolved, unresolved


# --- prose counts pinned to the register ------------------------------------

def test_primary_source_count_in_the_paper_matches_the_register() -> None:
    """§3 says twenty-three primary sources. The register must still say so."""
    import re

    text = (REPO_ROOT / "paper-text.md").read_text(encoding="utf-8")
    assert "Twenty-three primary sources" in text
    p_coded = [r["key"] for r in read_csv("sources.csv") if re.fullmatch(r"P\d+", r["key"])]
    assert len(p_coded) == 23, len(p_coded)


def test_framework_count_in_the_paper_matches_the_register() -> None:
    """§3 says eleven standards or frameworks."""
    text = (REPO_ROOT / "paper-text.md").read_text(encoding="utf-8")
    assert "eleven standards or frameworks" in text
    frameworks = [r["key"] for r in read_csv("sources.csv") if r["kind"] == "framework"]
    assert len(frameworks) == 11, len(frameworks)


def test_three_week_gap_is_computable_from_the_register() -> None:
    """§1 says three weeks after the Black Hat presentation; both dates are in the register.

    No author is named for the earlier account, because the register does not
    support one.
    """
    import datetime

    text = (REPO_ROOT / "paper-text.md").read_text(encoding="utf-8")
    assert "three weeks after the Black Hat presentation" in text
    by_key = {r["key"]: r for r in read_csv("sources.csv")}
    assert by_key["P1"]["date"] == "2026-08-26"
    assert by_key["P4"]["date"].startswith("2026-08-05")
    assert (datetime.date(2026, 8, 26) - datetime.date(2026, 8, 5)).days == 21


# --- the submission document ------------------------------------------------

def test_template_structure_is_recorded_from_the_file() -> None:
    text = (REPO_ROOT / "docs" / "paper-template.md").read_text(encoding="utf-8")
    assert "PENDING" not in text
    for anchor in (
        "Recommended length: 4 pages excluding references and appendix",
        "US Letter",
        "Arial 11 pt",
        "5. Discussion and Limitations",
        "LLM Usage Statement",
        "150–250 words",
    ):
        assert anchor in text, anchor


def test_submission_docx_is_built_from_the_template() -> None:
    import zipfile

    docx = REPO_ROOT / "output" / "paper.docx"
    assert docx.exists() and docx.stat().st_size > 50_000
    with zipfile.ZipFile(docx) as archive:
        names = archive.namelist()
        assert names[0] == "[Content_Types].xml", "content types must be the first entry"
        for part in ("word/document.xml", "word/styles.xml", "word/numbering.xml"):
            assert part in names, part
        # the four figures travelled into the package
        media = [n for n in names if n.startswith("word/media/")]
        assert len(media) == 2, media
        document = archive.read("word/document.xml").decode("utf-8")
    assert "PROJECT TITLE" not in document, "template placeholder survived"
    assert "Delete all guidance text" not in document, "guidance info box survived"
    assert "Bypassed, Not Broken" in document


# --- single authorship and the author details -------------------------------

def test_paper_uses_first_person_singular() -> None:
    """One author, so no editorial we. Quoted third-party 'we' is exempt."""
    import re

    text = (REPO_ROOT / "paper-text.md").read_text(encoding="utf-8")
    offenders = re.findall(r"\b(?:[Ww]e|[Oo]ur)\b", text)
    assert not offenders, offenders


def test_author_details_are_current() -> None:
    text = (REPO_ROOT / "paper-text.md").read_text(encoding="utf-8")
    assert "wagnernick1997@gmail.com" in text
    assert "partnernick1997" not in text
    assert "Apart-Research-Project-AI-Incident-Response-Sprint" in text
    assert "Nick-is-building/protection-time" not in text


def test_results_subsections_are_consecutive() -> None:
    """Merging 4.5 and 4.6 must not leave a hole in the numbering."""
    import re

    text = (REPO_ROOT / "paper-text.md").read_text(encoding="utf-8")
    numbers = [m.group(1) for m in re.finditer(r"^### 4\.(\d) ", text, re.M)]
    assert numbers == [str(n) for n in range(1, len(numbers) + 1)], numbers


def test_repository_pointer_appears_once() -> None:
    """The pointer belongs in Code and Data, not repeated in every appendix."""
    import assemble_paper

    text, _, _ = assemble_paper.build()
    assert text.count("reproduces every number in this paper") == 1
