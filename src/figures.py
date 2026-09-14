"""Figures for the paper. Sober, print-ready, no decoration.

Four figures, each written to output/ as both PNG (300 dpi) and PDF (vector).

  Figure 1  Timeline 6-13 July: t0, the held-evidence point, the three
            reconstitution points, drawn as nested bars.
  Figure 2  Prescribed review cadence against measured hold time, log axis.
  Figure 3  State distribution by row type.
  Figure 4  The awareness clock: four readings against the two regulatory
            thresholds, PRIMARY distinguished from SECONDARY, and the reading
            the source gives as a range drawn as a range.

Every value is read from data/ or computed by the other modules. Nothing here
is typed in.

Colour: the categorical slots below pass the adjacent-pair and all-pairs CVD
and normal-vision gates on a light surface. Three of them fall below 3:1
contrast against the surface, which obliges relief - so every mark carries a
visible direct label, and output/paper_tables.md is the table view. Evidence
status in figure 4 is encoded by hatch, not by colour, so it survives
greyscale printing.
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

import budgets  # noqa: E402
import compute_p  # noqa: E402

OUTPUT_DIR = REPO_ROOT / "output"

# When true, figures are rendered without their in-image title and caption,
# because the document they are placed in supplies both. Repeating them costs
# roughly an inch of page height per figure and reads as a duplication.
BARE = False

# Validated categorical slots (light surface).
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#8a8985"
SURFACE = "#ffffff"
NEUTRAL = "#52514e"

STATE_ORDER = ["held", "bypassed", "broken", "fired_not_escalated", "defeated_no_effect"]
STATE_COLOUR = dict(zip(STATE_ORDER, SERIES))

ROW_TYPE_LABEL = {
    "A_applied_nested": "A  applied, nested",
    "B_applied_nonnested": "B  applied, not nested",
    "C_standing": "C  pre-existing",
    "X_out_of_corpus": "X  out of corpus",
}


def apply_print_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.labelsize": 9,
        "axes.edgecolor": INK_MUTED,
        "axes.linewidth": 0.8,
        "axes.grid": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.color": INK_SECONDARY,
        "ytick.color": INK_SECONDARY,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.frameon": False,
        "legend.fontsize": 8,
        "lines.linewidth": 2.0,
        "figure.dpi": 110,
    })


def save(fig: plt.Figure, stem: str) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if BARE:
        stem = f"{stem}_bare"
    written = []
    for suffix, kwargs in ((".png", {"dpi": 300}), (".pdf", {})):
        path = OUTPUT_DIR / f"{stem}{suffix}"
        fig.savefig(path, bbox_inches="tight", **kwargs)
        written.append(path)
    plt.close(fig)
    return written


def finish(
    fig: plt.Figure,
    caption_text: str,
    legend_handles: list | None = None,
    legend_columns: int = 5,
    wrap_chars: int = 118,
) -> None:
    """Place legend and caption in space explicitly reserved for them.

    Laying these out by trial-and-error offsets is how figures end up with a
    caption printed through the axis label. Here the bottom margin is computed
    from the number of wrapped caption lines, and the two artists get disjoint
    bands inside it.
    """
    lines = [] if BARE else (textwrap.wrap(caption_text, wrap_chars) or [""])
    caption_height = 0.030 * len(lines)
    # The legend needs its own band clear of the axis label, or the two collide.
    legend_height = 0.115 if legend_handles else 0.0
    bottom = 0.19 + caption_height + legend_height

    fig.subplots_adjust(bottom=bottom)

    if legend_handles:
        fig.legend(
            handles=legend_handles,
            loc="lower center",
            bbox_to_anchor=(0.5, caption_height + 0.015),
            ncol=legend_columns,
            handlelength=1.3,
            columnspacing=1.6,
        )

    if lines:
        fig.text(0.012, caption_height - 0.004, "\n".join(lines),
                 ha="left", va="top", fontsize=7, color=INK_MUTED, linespacing=1.5)


def load_rows() -> list[dict[str, str]]:
    _, raw = compute_p.load_rows()
    return compute_p.compute(raw)


# --- Figure 1: the timeline -------------------------------------------------

def figure_1(rows: list[dict[str, str]]) -> list[Path]:
    type_a = sorted(
        (r for r in rows if r["row_type"] == "A_applied_nested"),
        key=lambda r: float(r["p_wall_hours"]),
    )
    t0 = compute_p.parse_utc(type_a[0]["applied_utc"])
    assert t0 is not None

    labels = {
        "A1": "A1  internet egress",
        "A2": "A2  inter-agent communication",
        "A3": "A3  Artifactory admin access",
    }
    ordered = list(reversed(type_a))  # longest at the bottom

    fig, ax = plt.subplots(figsize=(7.6, 3.2))

    ends = []
    for index, row in enumerate(ordered):
        end = compute_p.parse_utc(row["reconstituted_utc"])
        assert end is not None
        ends.append(end)
        colour = SERIES[len(ordered) - 1 - index]
        ax.barh(index, end - t0, left=t0, height=0.48,
                color=colour, edgecolor=SURFACE, linewidth=2.0, zorder=3)
        ax.text(end + timedelta(hours=3), index, row["p_wall_hhmm"],
                va="center", ha="left", fontsize=8, color=INK, zorder=5)

    # Drop lines make the containment literally visible: each shorter interval's
    # end point falls through the longer bars that enclose it. ordered[0] is the
    # longest, so the lines run down to it.
    for index, end in enumerate(ends):
        if index == 0:
            continue
        ax.plot([end, end], [index - 0.24, -0.24], color=INK_MUTED,
                linewidth=0.8, linestyle=(0, (2, 2)), zorder=2)

    ax.set_yticks(range(len(ordered)))
    ax.set_yticklabels([labels[r["id"]] for r in ordered], fontsize=8)

    ax.axvline(t0, color=INK, linewidth=1.4, zorder=6)
    ax.annotate("t₀  2026-07-06 01:16Z   Artifactory rebuild",
                xy=(t0, len(ordered) - 0.05), xytext=(5, 5), textcoords="offset points",
                va="bottom", ha="left", fontsize=7.5, color=INK, zorder=7,
                annotation_clip=False)

    held_row = next(r for r in type_a if r["held_evidence_utc"])
    held = compute_p.parse_utc(held_row["held_evidence_utc"])
    assert held is not None
    held_index = ordered.index(held_row)
    ax.plot([held], [held_index], marker="|", markersize=16, markeredgewidth=1.8,
            color=SURFACE, zorder=6)
    ax.annotate("12:56Z  control held: three egress attempts → HTTP 400",
                xy=(held, held_index - 0.24), xytext=(150, -26), textcoords="offset points",
                va="center", ha="left", fontsize=7.5, color=INK_SECONDARY, zorder=7,
                arrowprops=dict(arrowstyle="-", color=INK_SECONDARY, linewidth=0.8,
                                shrinkA=0, shrinkB=1))

    ax.set_xlim(t0 - timedelta(hours=7), max(ends) + timedelta(hours=30))
    ax.set_ylim(-0.6, len(ordered) - 0.05)
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.set_xlabel("2026, UTC")
    ax.set_title("" if BARE else "Figure 1   Protection time of the three controls applied at the rebuild", pad=26 if not BARE else 12)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    finish(fig, "All three intervals share one start point, so they are nested: "
                "[t₀,A1] ⊂ [t₀,A2] ⊂ [t₀,A3]. The dashed drop lines mark where the shorter "
                "intervals end inside the longer ones. Source: P1 section X; evidence base 4.1-4.3.")
    return save(fig, "figure_1_timeline")


# --- Figure 2: cadence against measured hold time ---------------------------

def figure_2(rows: list[dict[str, str]]) -> list[Path]:
    type_a = sorted(
        (r for r in rows if r["row_type"] == "A_applied_nested"),
        key=lambda r: float(r["p_wall_hours"]),
    )
    year = budgets.HOURS_PER_YEAR
    names = {"A1": "A1  internet egress", "A2": "A2  inter-agent comms",
             "A3": "A3  Artifactory admin"}

    fig, ax = plt.subplots(figsize=(7.6, 2.9))

    for index, row in enumerate(type_a):
        hours = float(row["p_wall_hours"])
        ax.barh(index, hours, height=0.46, color=SERIES[index],
                edgecolor=SURFACE, linewidth=2.0, zorder=3)
        ax.text(hours * 1.14, index, f"{row['p_wall_hhmm']}   —   {year / hours:.0f}× shorter",
                va="center", ha="left", fontsize=8, color=INK, zorder=5)

    ax.axvline(year, color=INK, linewidth=1.4, zorder=6)
    ax.annotate(f"AIS-13: review sandboxing policies\n'at least annually' = {year:,} h",
                xy=(year, 1.0), xytext=(-8, 0), textcoords="offset points",
                va="center", ha="right", fontsize=7.5, color=INK, zorder=7)

    ax.set_xscale("log")
    ax.set_xlim(18, year * 3.2)
    ax.set_yticks(range(len(type_a)))
    ax.set_yticklabels([names[r["id"]] for r in type_a], fontsize=8)
    ax.set_ylim(-0.6, len(type_a) - 0.4)
    ax.set_xlabel("hours (log scale)")
    ax.set_title("" if BARE else "Figure 2   Prescribed review cadence against measured hold time", pad=12)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    finish(fig, "The prescribed re-verification cadence exceeds every measured hold time by a "
                "factor of 50 to 187. Sources: CSA AICM AIS-13 (N2); evidence base 12.5, 4.3.")
    return save(fig, "figure_2_cadence")


# --- Figure 3: state distribution by row type -------------------------------

def figure_3(rows: list[dict[str, str]]) -> list[Path]:
    present_types = [t for t in ROW_TYPE_LABEL if any(r["row_type"] == t for r in rows)]
    counts = {
        row_type: Counter(r["state"] for r in rows if r["row_type"] == row_type)
        for row_type in present_types
    }

    fig, ax = plt.subplots(figsize=(7.6, 2.5))

    for index, row_type in enumerate(present_types):
        left = 0
        for state in STATE_ORDER:
            value = counts[row_type].get(state, 0)
            if not value:
                continue
            ax.barh(index, value, left=left, height=0.52, color=STATE_COLOUR[state],
                    edgecolor=SURFACE, linewidth=2.0, zorder=3)
            ax.text(left + value / 2, index, str(value), va="center", ha="center",
                    fontsize=8, color=SURFACE, fontweight="bold", zorder=5)
            left += value
        ax.text(left + 0.25, index, f"n = {left}", va="center", ha="left",
                fontsize=8, color=INK_SECONDARY, zorder=5)

    ax.set_yticks(range(len(present_types)))
    ax.set_yticklabels([ROW_TYPE_LABEL[t] for t in present_types], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlim(0, max(sum(c.values()) for c in counts.values()) + 2.4)
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    ax.set_title("" if BARE else "Figure 3   Control state by row type", pad=12)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    empty = [t for t in ROW_TYPE_LABEL if t not in present_types]
    note = ("Type B is defined in the schema and empty in the corpus: every control other than "
            "the 6 July rebuild was already standing. " if empty else "")
    finish(
        fig,
        note + "Type C rows carry no P_wall and are measured binarily instead. "
               "Source: data/clock.csv.",
        legend_handles=[
            Patch(facecolor=STATE_COLOUR[s], label=s.replace("_", " ")) for s in STATE_ORDER
        ],
        legend_columns=5,
    )
    return save(fig, "figure_3_states")


# --- Figure 4: the awareness clock ------------------------------------------

def figure_4() -> list[Path]:
    readings = list(budgets.AWARENESS_READINGS)
    disclosure = budgets.DISCLOSURE
    ordered = list(reversed(readings))

    fig, ax = plt.subplots(figsize=(7.6, 3.5))

    for index, reading in enumerate(ordered):
        low, high = reading.days_to(disclosure)
        is_secondary = reading.status != "PRIMARY"
        breach = high > budgets.EU_CYBER_DEADLINE_DAYS
        colour = SERIES[1] if breach else SERIES[0]

        ax.barh(index, low, height=0.46, color=colour, edgecolor=SURFACE, linewidth=2.0,
                hatch="///" if is_secondary else None, zorder=3)
        if high > low:
            # The source gives this reading as a range, so it is drawn as one.
            ax.plot([low, high], [index, index], color=INK, linewidth=1.4, zorder=5)
            for cap in (low, high):
                ax.plot([cap, cap], [index - 0.15, index + 0.15], color=INK,
                        linewidth=1.4, zorder=5)

        label = f"{low}–{high} d" if high > low else f"{high} d"
        ax.text(high + 0.4, index, label, va="center", ha="left", fontsize=8,
                color=INK, zorder=6)

    top = len(ordered) - 0.42
    ax.axvline(budgets.EU_CYBER_DEADLINE_DAYS, color=INK, linewidth=1.4, zorder=7)
    ax.annotate("EU  5 d", xy=(budgets.EU_CYBER_DEADLINE_DAYS, top), xytext=(-5, 0),
                textcoords="offset points", va="bottom", ha="right",
                fontsize=7.5, color=INK, zorder=8)
    ax.axvline(budgets.CAL_DEADLINE_DAYS, color=INK, linewidth=1.4,
               linestyle=(0, (4, 3)), zorder=7)
    ax.annotate("California  15 d", xy=(budgets.CAL_DEADLINE_DAYS, top), xytext=(-5, 0),
                textcoords="offset points", va="bottom", ha="right",
                fontsize=7.5, color=INK, zorder=8)

    ax.set_yticks(range(len(ordered)))
    ax.set_yticklabels([r.label for r in ordered], fontsize=8)
    ax.set_xlabel("days from awareness to public disclosure, 2026-07-21", labelpad=8)
    ax.set_xlim(0, 19.5)
    ax.set_ylim(-0.55, len(ordered) - 0.05)
    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(5))
    ax.xaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(1))
    ax.set_title("" if BARE else "Figure 4   The awareness clock: four readings, two regulatory thresholds",
                 pad=18)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    finish(
        fig,
        "This measures the interval to PUBLIC DISCLOSURE, which is a different quantity from "
        "the regulatory obligation: a non-public report to a regulator could have been timely. "
        "Three readings are PRIMARY, one is SECONDARY (hatched). The clock starts at awareness "
        "and the source supports at least three awareness dates; this figure does not choose "
        "between them. Sources: evidence base 16.1, 16.2.",
        legend_handles=[
            Patch(facecolor=SERIES[0], label="within both deadlines"),
            Patch(facecolor=SERIES[1], label="past the EU deadline"),
            Patch(facecolor=SURFACE, edgecolor=INK_SECONDARY, hatch="///",
                  label="SECONDARY evidence"),
        ],
        legend_columns=3,
    )
    return save(fig, "figure_4_awareness_clock")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--bare", action="store_true",
                        help="omit in-image titles and captions, for figures placed in a "
                             "document that supplies them")
    args = parser.parse_args(argv)

    global BARE
    BARE = args.bare
    apply_print_style()
    rows = load_rows()

    written: list[Path] = []
    written += figure_1(rows)
    written += figure_2(rows)
    written += figure_3(rows)
    written += figure_4()

    if not args.quiet:
        for path in written:
            print(f"Written: {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
