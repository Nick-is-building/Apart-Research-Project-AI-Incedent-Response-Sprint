"""Assemble output/paper.md from paper-text.md and the repository data.

The prose in paper-text.md is authored and is copied through unchanged. This
module only does two things to it:

  1. Replaces the six [Claude Code: ...] markers with generated content, drawn
     from the file each marker names. Nothing in those six sections is typed.
  2. Places the four figures at the points the text supports.

The official submission template is NOT applied here: it has not been read
(see docs/paper-template.md). This produces the complete paper content, ready
to be poured into the template once it is available.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

SOURCE_TEXT = REPO_ROOT / "paper-text.md"
OUTPUT_MD = REPO_ROOT / "output" / "paper.md"
DATA = REPO_ROOT / "data"
DOCS = REPO_ROOT / "docs"

MARKER = re.compile(r"^\*\[Claude Code: .*?\]\*$", re.M | re.S)


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def escape(text: str) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def truncate(text: str, limit: int) -> str:
    text = (text or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip(" ,;") + "…"


def demote(markdown: str, levels: int = 2) -> str:
    """Push headings down so an inserted document nests under its appendix."""
    out = []
    for line in markdown.splitlines():
        if line.startswith("#"):
            hashes = len(line) - len(line.lstrip("#"))
            line = "#" * min(hashes + levels, 6) + line[hashes:]
        out.append(line)
    return "\n".join(out)


POINTER = ("Full text in the repository; `./verify.sh` reproduces every number in this "
           "paper from the raw data.")


# --- Appendix A: the clause, at specification length ------------------------

def appendix_a() -> str:
    text = (DOCS / "clause-ais-13-m.md").read_text(encoding="utf-8")
    block = text[text.index("### Control Specification"):text.index("**Elimination, defined.**")]
    specification = " ".join(
        line.lstrip("> ").strip() for line in block.splitlines()
        if line.strip().startswith(">")
    ).strip()

    return "\n".join([
        "**AIS-13.M — Capability Mechanism Inventory and Protection-Time Budget** extends CSA "
        "AI Controls Matrix v1.1.1 AIS-13, which already requires an inventory and a "
        "completeness check — of components that execute, not of mechanisms by which a "
        "capability is realised.",
        "",
        "> " + specification,
        "",
        "The audit is document-based and needs no network access: a mechanism visible in the "
        "operator's own architecture documentation but absent from the inventory is a finding. "
        "Normative text, guidelines, mapping and cost section are in "
        "`docs/clause-ais-13-m.md`. " + POINTER,
    ])


# --- Appendix B: contradictions, table only ---------------------------------

def appendix_b() -> str:
    rows = read_csv("contradictions.csv")
    intra = sum(1 for r in rows if r["intra_document"] == "TRUE")
    out = [
        f"{len(rows)} documented contradictions, {intra} of them inside a single document. "
        f"Both quoted claims per row, and the full resolving questions, are in "
        f"`data/contradictions.csv`. " + POINTER,
        "",
        "| | Contradiction | Intra-doc | Resolving question |",
        "|---|---|---|---|",
    ]
    for row in rows:
        out.append(
            f"| {row['id']} | {escape(row['short_title'])} "
            f"| {'yes' if row['intra_document'] == 'TRUE' else 'no'} "
            f"| {escape(truncate(row['resolving_question'], 66))} |"
        )
    return "\n".join(out)


# --- Appendix C: one sentence per limitation --------------------------------

LIMITATION_SENTENCES = [
    ("`P_exp` magnitude", "No public document records when evaluation workloads ran, so no "
     "exposure-normalised magnitude is reported and only the ordering of the three follows."),
    ("One incident", "The comparison cases are a contrast class, not an out-of-sample test: "
     "internet access was open there by misconfiguration or design, so protection time is "
     "undefined, not zero."),
    ("Transcript integrity", "METR found spoofed tool calls in at least 96 transcripts against "
     "OpenAI's statement that none affected the logs its graders see — unresolved here, and "
     "every protection time inherits it."),
    ("Standing rows", "Sixteen of the twenty-two rows are pre-existing controls with no "
     "application event, so they carry no protection time and are measured binarily."),
    ("One undeterminable state", "For the host-mount restriction the report records only that "
     "one pod failed and a second succeeded, so `broken` is as much a claim as `bypassed`."),
    ("Uneven instrument evidence", "Eleven of the seventeen instruments were established by "
     "term count and six by qualitative reading, so a headline should use eleven."),
    ("The awareness clock", "Those figures measure the interval to public disclosure, not to "
     "regulatory filing: a non-public report could have been timely on any reading."),
]


def appendix_c() -> str:
    out = [f"**{name}.** {sentence}" for name, sentence in LIMITATION_SENTENCES]
    out.append("")
    out.append("Extended version, including what would change the result, in "
               "`docs/limitations.md`. " + POINTER)
    return "\n\n".join(out)


# --- Appendix E: minimum data for external measurement ----------------------

MINIMUM_FIELDS = [
    ("Control identifier", "supplied"),
    ("Capability blocked, stated as an outcome", "partly — assumed for some rows, flagged"),
    ("Application timestamp, to the minute", "supplied, for one event only"),
    ("Evidence the control was active", "partly — egress only, three HTTP 400 responses"),
    ("Realisation timestamp, to the minute", "supplied, for all three measured rows"),
    ("Mechanism used", "partly — not named for egress"),
    ("Workload activity intervals over the window", "**not supplied**"),
]


def appendix_e() -> str:
    out = [
        "The fields an external party needs to compute a protection time, and whether the "
        "OpenAI record supplies them.",
        "",
        "| Field | In the record |",
        "|---|---|",
    ]
    out += [f"| {name} | {status} |" for name, status in MINIMUM_FIELDS]
    out += [
        "",
        "Six of the seven are present for at least some rows, which is why three protection "
        "times can be computed at all. The seventh is absent, and that is why no "
        "exposure-normalised magnitude is reported. A harness emitting these seven fields would "
        "make the quantity measurable by default rather than recoverable by archaeology.",
    ]
    return "\n".join(out)


# --- References -------------------------------------------------------------

# The main text carries [1]-[6] by hand; these continue the list. Each entry
# names the source code it is drawn from in data/sources.csv.
REFERENCE_CODES = [
    "P1", "P2", "P3", "P5", "N11", "P10", "P7", "P8", "N1", "N2", "N3",
    "P15", "P16", "S03", "P19", "P24", "N7", "N5", "N6", "N4", "P25",
]


def references() -> str:
    by_key = {r["key"]: r for r in read_csv("sources.csv")}
    missing = [c for c in REFERENCE_CODES if c not in by_key]
    if missing:
        raise ValueError(f"reference codes absent from sources.csv: {missing}")

    out = [
        "*Entries [7] onward generated from `data/sources.csv`.*",
        "",
    ]
    for index, code in enumerate(REFERENCE_CODES, start=7):
        row = by_key[code]
        parts = [f"[{index}]"]
        if row["organisation"]:
            parts.append(f"{row['organisation']}.")
        parts.append(f"{row['title']}.")
        parts.append(f"{row['date']}.")
        if row["url"]:
            parts.append(row["url"])
        else:
            parts.append("(no public URL recorded; see `data/sources.csv`)")
        out.append(" ".join(parts))
        out.append("")
    return "\n".join(out).rstrip()


# --- figures ----------------------------------------------------------------

FIGURES = {
    "### 4.1 Three protection times, verified to the minute": (
        "![Figure 1](figure_1_timeline_bare.png)\n\n"
        "**Figure 1.** Protection time of the three controls applied at the Artifactory "
        "rebuild. The intervals share one start point, so they are nested: "
        "[t₀,A1] ⊂ [t₀,A2] ⊂ [t₀,A3]; dashed lines mark where the shorter ones end."
    ),
    "### 4.5 The declared cadence and the declared response budget are both exceeded by the measured values": (
        "![Figure 4](figure_4_awareness_clock_bare.png)\n\n"
        "**Figure 4.** The awareness clock: four readings of when OpenAI became aware, against "
        "the EU five-day and California fifteen-day thresholds. This measures the interval to "
        "public disclosure, a different quantity from the regulatory obligation. Three readings "
        "are primary, one secondary (hatched)."
    ),
}
# Figures 2 and 3 live in Appendix H, placed by appendix_h() rather than here.


def place_figures(text: str) -> tuple[str, list[str]]:
    """Insert each figure at the end of the subsection its content supports."""
    placed: list[str] = []
    lines = text.splitlines()
    out: list[str] = []
    pending: str | None = None

    for line in lines:
        starts_new_section = line.startswith("#")
        if pending and starts_new_section:
            out += ["", pending, ""]
            pending = None
        out.append(line)
        if line.strip() in FIGURES:
            pending = FIGURES[line.strip()]
            placed.append(line.strip())
    if pending:
        out += ["", pending, ""]
    return "\n".join(out), placed


# --- assembly ---------------------------------------------------------------

GENERATORS = [
    ("Appendix A", "clause-ais-13-m.md", appendix_a),
    ("Appendix B", "contradictions.csv", appendix_b),
    ("Appendix C", "limitations.md", appendix_c),
    ("Appendix E", "generated table", appendix_e),
    ("References", "sources.csv", references),
]


def build() -> tuple[str, list[str], list[str]]:
    text = SOURCE_TEXT.read_text(encoding="utf-8")

    markers = MARKER.findall(text)
    if len(markers) != len(GENERATORS):
        raise ValueError(f"expected {len(GENERATORS)} markers, found {len(markers)}")

    filled: list[str] = []
    for (name, source, generator), marker in zip(GENERATORS, markers):
        text = text.replace(marker, generator(), 1)
        filled.append(f"{name} <- {source}")

    if MARKER.search(text):
        raise ValueError("a [Claude Code: ...] marker survived assembly")

    text, placed = place_figures(text)
    return text, filled, placed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUTPUT_MD)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    text, filled, placed = build()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")

    if not args.quiet:
        print(f"Written: {args.out.relative_to(REPO_ROOT)}")
        print(f"  generated sections: {len(filled)}")
        for entry in filled:
            print(f"    {entry}")
        print(f"  figures placed: {len(placed)}")
        words = len(text.split())
        print(f"  total words (including appendices): {words:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
