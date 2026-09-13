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


def demote(markdown: str, levels: int = 2) -> str:
    """Push headings down so an inserted document nests under its appendix."""
    out = []
    for line in markdown.splitlines():
        if line.startswith("#"):
            hashes = len(line) - len(line.lstrip("#"))
            line = "#" * min(hashes + levels, 6) + line[hashes:]
        out.append(line)
    return "\n".join(out)


# --- Appendix A: the clause, sections 2 to 7 --------------------------------

def appendix_a() -> str:
    text = (DOCS / "clause-ais-13-m.md").read_text(encoding="utf-8")
    body = text[text.index("## 2. Control row (AICM format)"):].rstrip()
    header = (
        "*Inserted verbatim from `docs/clause-ais-13-m.md`, sections 2 through 7. "
        "Section 1, the design rationale, is omitted: it restates the argument of "
        "Section 5 above.*\n\n"
    )
    return header + demote(body, levels=1)


# --- Appendix B: the contradiction register ---------------------------------

def appendix_b() -> str:
    rows = read_csv("contradictions.csv")
    intra = sum(1 for r in rows if r["intra_document"] == "TRUE")
    main = [r["id"] for r in rows if r["in_paper_main_text"] == "TRUE"]

    out = [
        f"*Generated from `data/contradictions.csv`. {len(rows)} documented contradictions, "
        f"{intra} of them intra-document — inside a single document. "
        f"{', '.join(main)} are discussed in the main text; all {len(rows)} are carried here.*",
        "",
    ]
    for row in rows:
        out.append(f"**{row['id']} — {row['short_title']}**"
                   + ("  ·  *main text*" if row["in_paper_main_text"] == "TRUE" else ""))
        out.append("")
        kind = "intra-document" if row["intra_document"] == "TRUE" else "between documents"
        out.append(f"*{kind}; status {row['status']}*")
        out.append("")
        out.append(f"- **{escape(row['source_a'])}:** {escape(row['claim_a'])}")
        out.append(f"- **{escape(row['source_b'])}:** {escape(row['claim_b'])}")
        out.append(f"- **Resolving question:** {escape(row['resolving_question'])}")
        out.append("")
    return "\n".join(out).rstrip()


# --- Appendix C: extended limitations ---------------------------------------

def appendix_c() -> str:
    text = (DOCS / "limitations.md").read_text(encoding="utf-8")
    body = text[text.index("\n", text.index("# Limitations")):].strip()
    header = "*Inserted from `docs/limitations.md`.*\n\n"
    return header + demote(body, levels=1)


# --- Appendix E: what did not work ------------------------------------------

# Drawn from evidence base section 19. Only the errors that changed a number or
# a conclusion; the full nineteen are in docs/belegbasis-v3.md section 19.
CORRECTIONS = [
    (
        "The rebuild date, which would have moved all three values by two days",
        "OpenAI's blog post of 26 August dates the Artifactory rebuild to 8 July. Its own "
        "technical report dates it to 2026-07-06 01:16 UTC, and three further sources agree: "
        "the report's narrative section, the Black Hat transcript in which an OpenAI engineer "
        "says \"The date at this point is July 6\", and METR's chronology. Taking the blog "
        "post's date would have shortened every protection time in this paper by 48 hours. "
        "Carried as W-8, resolved against the blog post.",
        "Where two artefacts from the same organisation on the same day disagree, the one with "
        "the timestamped appendix wins, and the disagreement is recorded rather than silently "
        "resolved.",
    ),
    (
        "A false absence claim caused by date formatting",
        "We asserted that 20 April does not appear in the technical report. It does, as the "
        "first row of the event table: `2026-04-20 07:59 UTC`. The search had been run for "
        "\"April\" against a document that uses ISO dates.",
        "A negative finding is only as good as the search terms. Every \"does not appear\" "
        "claim was re-run across spellings and formats, and the second pass over the METR "
        "investigation was carried out for this reason.",
    ),
    (
        "Two register lines recommended for deletion that were genuine",
        "We twice proposed dropping a contradiction as resolvable. The ChatGPT/Codex harness "
        "attribution (W-3) appears in two places in the same report about five pages apart, "
        "and the transcript-integrity conflict (W-4) is a direct clash between OpenAI's "
        "blanket statement and METR's counts. Both are real and both remain in the register.",
        "The error direction was constant across the project: over-confident resolution, never "
        "invention. That asymmetry is itself a finding about how this material fails.",
    ),
    (
        "Two rows reclassified from applied to standing, removing a row type",
        "The outbound network controls and the Artifactory image-cache integrity handling were "
        "first recorded as controls applied on 9 July. That was wrong: 9 July is when the "
        "event occurred, not when the control was applied, and both were already standing. "
        "They moved from B1 and B2 to C15 and C16, and the row type \"applied, not nested\" "
        "became empty.",
        "This produced the finding in Section 3: the entire public record contains exactly one "
        "control-application event. The correction did not weaken the result, it produced it.",
    ),
]


def appendix_e() -> str:
    out = [
        "*Selected from the correction history in the evidence base, section 19, which records "
        "nineteen errors from the research process with their methodological causes. The four "
        "below are those that changed a number or a conclusion. The full list is in the "
        "repository and is deliberately not summarised into something flattering.*",
        "",
    ]
    for index, (title, what, lesson) in enumerate(CORRECTIONS, start=1):
        out += [f"**E.{index} {title}**", "", what, "", f"*What this changed:* {lesson}", ""]
    return "\n".join(out).rstrip()


# --- Appendix F: minimum data for external measurement ----------------------

MINIMUM_FIELDS = [
    ("Control identifier",
     "A stable name for the control, so successive applications can be told apart",
     "yes", "Named in the narrative and in the event table"),
    ("Capability blocked, stated as an outcome",
     "What the control is credited with preventing, expressed as a result rather than as a "
     "request type",
     "partly", "Stated for some controls; for others it had to be assumed and is flagged "
               "as a project assumption in `data/clock.csv`"),
    ("Application timestamp, to the minute",
     "When the control took effect. Without it there is no interval and no protection time",
     "yes", "2026-07-06 01:16 UTC, for one event only"),
    ("Evidence the control was active",
     "A positive observation that the control was doing something after application",
     "partly", "Present for egress only: three HTTP 400 responses at 12:56 UTC"),
    ("Realisation timestamp, to the minute",
     "When the blocked capability was first achieved by any mechanism",
     "yes", "For all three measured rows"),
    ("Mechanism used",
     "Which route realised the capability, so it can be checked against an inventory",
     "partly", "Named for inter-agent communication and administrator access; not named for "
               "egress, which is why that row's `alternative_mechanism` is left empty"),
    ("Workload activity intervals over the measurement window",
     "When evaluation workloads actually ran, so calendar time can be normalised to exposure",
     "no", "**Absent entirely.** No public document records when workloads ran or paused "
           "between 6 and 7 July"),
]


def appendix_f() -> str:
    supplied = {"yes": "supplied", "partly": "partly supplied", "no": "**not supplied**"}
    out = [
        "*Generated. The fields an external party needs to compute a protection time, and "
        "whether the OpenAI record supplies them.*",
        "",
        "| Field | Why it is required | In the record | Detail |",
        "|---|---|---|---|",
    ]
    for name, why, status, detail in MINIMUM_FIELDS:
        out.append(f"| {name} | {why} | {supplied[status]} | {detail} |")
    out += [
        "",
        "Six of the seven are present for at least some rows, which is why three protection "
        "times can be computed at all. The seventh is absent, and that absence is the reason "
        "no exposure-normalised magnitude is reported anywhere in this paper: only the "
        "ordering of the exposure-normalised times follows, and it follows deductively from "
        "the nesting rather than from data. A harness that emitted these seven fields would "
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
        "*Entries [7] onward generated from `data/sources.csv`; the bracketed code after each "
        "is its identifier in that register.*",
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
        parts.append(f"[{code}]")
        out.append(" ".join(parts))
        out.append("")
    return "\n".join(out).rstrip()


# --- figures ----------------------------------------------------------------

FIGURES = {
    "### 4.1 Three protection times, verified to the minute": (
        "after_block",
        "![Figure 1](figure_1_timeline.png)\n\n"
        "**Figure 1.** Protection time of the three controls applied at the Artifactory "
        "rebuild. All three intervals share one start point, so they are nested: "
        "[t₀,A1] ⊂ [t₀,A2] ⊂ [t₀,A3]. The dashed drop lines mark where the shorter intervals "
        "end inside the longer ones. Source: `output/figure_1_timeline.pdf`.",
    ),
    "### 4.5 The required re-verification cadence exceeds the measured hold times by two orders of magnitude": (
        "after_block",
        "![Figure 2](figure_2_cadence.png)\n\n"
        "**Figure 2.** Prescribed review cadence against measured hold time, log axis. "
        "Source: `output/figure_2_cadence.pdf`.",
    ),
    "### 4.7 No instrument records how long a control holds": (
        "after_block",
        "![Figure 3](figure_3_states.png)\n\n"
        "**Figure 3.** Control state by row type across the 22-row clock. Type B is defined in "
        "the schema and empty in the corpus. Source: `output/figure_3_states.pdf`.",
    ),
    "### 4.6 The declared response budget was exceeded by a factor of eleven": (
        "after_block",
        "![Figure 4](figure_4_awareness_clock.png)\n\n"
        "**Figure 4.** The awareness clock: four readings of when OpenAI became aware, against "
        "the EU five-day and California fifteen-day thresholds. Measures the interval to public "
        "disclosure, which is a different quantity from the regulatory obligation. Three "
        "readings are primary, one secondary (hatched). Source: "
        "`output/figure_4_awareness_clock.pdf`.",
    ),
}


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
            _, caption = FIGURES[line.strip()]
            pending = caption
            placed.append(line.strip())
    if pending:
        out += ["", pending, ""]
    return "\n".join(out), placed


# --- assembly ---------------------------------------------------------------

GENERATORS = [
    ("Appendix A", "clause-ais-13-m.md", appendix_a),
    ("Appendix B", "contradictions.csv", appendix_b),
    ("Appendix C", "limitations.md", appendix_c),
    ("Appendix E", "belegbasis-v3.md section 19", appendix_e),
    ("Appendix F", "generated table", appendix_f),
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
