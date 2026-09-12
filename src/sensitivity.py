"""The nesting argument for P_exp, and the parameter space around it.

The three type-A controls were all applied at the same instant, t0 =
2026-07-06T01:16Z.  Their intervals therefore share a start point and differ
only in where they end, which makes them nested:

    [t0, t_A1]  subset  [t0, t_A2]  subset  [t0, t_A3]

If P_exp is the integral of agent execution activity over the respective
interval, and that activity is nowhere negative, then

    P_exp(A1) <= P_exp(A2) <= P_exp(A3)

follows necessarily, for ANY duty-cycle function - not only constant ones.
The integral of a non-negative function over a larger set cannot be smaller
than over a subset of it.  That is the whole argument; it needs no data about
when workloads actually ran.

This module does four things:

  1. Verifies the nesting FROM THE DATA rather than assuming it.
  2. Runs a Monte Carlo demonstration over random non-negative duty cycles.
     This is an illustration of the proof, not a proof.
  3. Shows that the nesting breaks as soon as rows with a different
     applied_utc are admitted.
  4. Maps the parameter space of the per-control alpha model, which is the
     wrong model for these three rows, and shows what it would wrongly permit.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

import compute_p  # noqa: E402

OUTPUT_TXT = REPO_ROOT / "output" / "sensitivity_report.txt"

RULE = "=" * 78
THIN = "-" * 78


@dataclass(frozen=True)
class TypeARow:
    row_id: str
    control: str
    applied: datetime
    reconstituted: datetime

    @property
    def p_wall_hours(self) -> float:
        return (self.reconstituted - self.applied).total_seconds() / 3600.0


def load_type_a(clock_csv: Path = compute_p.CLOCK_CSV) -> list[TypeARow]:
    _, rows = compute_p.load_rows(clock_csv)
    out: list[TypeARow] = []
    for row in rows:
        if row["row_type"] != "A_applied_nested":
            continue
        applied = compute_p.parse_utc(row["applied_utc"])
        reconstituted = compute_p.parse_utc(row["reconstituted_utc"])
        if applied is None or reconstituted is None:
            raise ValueError(f"row {row['id']}: type A requires two dated timestamps")
        out.append(TypeARow(row["id"], row["control"], applied, reconstituted))
    return sorted(out, key=lambda r: r.reconstituted)


# --- 1. verify the nesting --------------------------------------------------

def verify_nesting(rows: list[TypeARow]) -> tuple[bool, list[str]]:
    """Check the two conditions the argument rests on, from the data."""
    lines: list[str] = []
    ok = True

    starts = {r.applied for r in rows}
    if len(starts) == 1:
        lines.append(f"  [ok]   all {len(rows)} type-A rows share one applied_utc: "
                     f"{next(iter(starts)).strftime('%Y-%m-%dT%H:%MZ')}")
    else:
        ok = False
        lines.append(f"  [FAIL] type-A rows do not share one applied_utc: "
                     f"{sorted(s.isoformat() for s in starts)}")

    ends = [r.reconstituted for r in rows]
    if all(a < b for a, b in zip(ends, ends[1:])):
        chain = "  subset  ".join(f"[t0, t_{r.row_id}]" for r in rows)
        lines.append(f"  [ok]   end points strictly ascending, so the intervals nest:")
        lines.append(f"         {chain}")
    else:
        ok = False
        lines.append("  [FAIL] end points are not strictly ascending; the intervals do not nest")

    return ok, lines


# --- 2. Monte Carlo demonstration -------------------------------------------

DUTY_CYCLE_FAMILIES = (
    "piecewise_constant",
    "bursty_spikes",
    "smooth_oscillating",
    "front_loaded",
    "back_loaded",
    "long_idle_then_burst",
)


def draw_duty_cycle(family: str, grid: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """A random non-negative duty cycle on `grid` (hours since t0).

    Non-negativity is the only property the proof needs.  The families differ
    wildly in shape on purpose: if the ordering survived only for well-behaved
    activity profiles, the argument would be worth much less.
    """
    n = grid.size
    span = float(grid[-1])

    if family == "piecewise_constant":
        n_blocks = int(rng.integers(2, 40))
        edges = np.sort(rng.uniform(0.0, span, size=n_blocks - 1))
        levels = rng.exponential(1.0, size=n_blocks)
        values = np.searchsorted(edges, grid)
        duty = levels[values]
    elif family == "bursty_spikes":
        duty = np.zeros(n)
        for _ in range(int(rng.integers(1, 30))):
            centre = rng.uniform(0.0, span)
            width = rng.uniform(0.05, 4.0)
            height = rng.exponential(5.0)
            duty += height * np.exp(-0.5 * ((grid - centre) / width) ** 2)
    elif family == "smooth_oscillating":
        duty = np.zeros(n)
        for _ in range(int(rng.integers(1, 8))):
            period = rng.uniform(1.0, 48.0)
            phase = rng.uniform(0.0, 2 * np.pi)
            duty += np.sin(2 * np.pi * grid / period + phase)
        duty = np.abs(duty)  # rectified: non-negative, still wildly varying
    elif family == "front_loaded":
        duty = rng.exponential(1.0) * np.exp(-grid / rng.uniform(1.0, 20.0))
    elif family == "back_loaded":
        duty = rng.exponential(1.0) * np.exp((grid - span) / rng.uniform(1.0, 20.0))
    elif family == "long_idle_then_burst":
        # Adversarial: all activity crammed into the tail, after A1 and A2 ended.
        start = rng.uniform(0.6 * span, 0.99 * span)
        duty = np.where(grid >= start, rng.exponential(10.0), 0.0)
    else:
        raise ValueError(f"unknown duty-cycle family: {family}")

    duty = np.clip(duty, 0.0, None)
    if not np.any(duty > 0):
        duty = np.full(n, 1e-9)
    return duty


def build_grid(bounds: list[float], grid_points: int) -> np.ndarray:
    """Integration grid containing every interval bound exactly.

    Putting the bounds on the grid means each interval ends where it really
    ends, not at the nearest sample below it.
    """
    base = np.linspace(0.0, max(bounds), grid_points)
    return np.unique(np.concatenate([base, np.asarray(bounds, dtype=float)]))


def cumulative_exposure(grid: np.ndarray, duty: np.ndarray) -> np.ndarray:
    """Cumulative trapezoidal integral of `duty`, aligned with `grid`.

    Written as a cumulative sum of per-segment increments rather than as an
    independent integral per interval.  Every increment of a non-negative duty
    cycle is non-negative, and in IEEE round-to-nearest arithmetic adding a
    non-negative number never decreases a running sum.  The result is therefore
    monotone non-decreasing *by construction*, which is what the proof says it
    must be - see `integrate_to` for what happens without this.
    """
    increments = 0.5 * (duty[1:] + duty[:-1]) * np.diff(grid)
    return np.concatenate([[0.0], np.cumsum(increments)])


def exposure_at(grid: np.ndarray, cumulative: np.ndarray, upper: float) -> float:
    """Exposure accumulated up to `upper`, which must lie on the grid."""
    index = int(np.searchsorted(grid, upper))
    return float(cumulative[index])


def integrate_to(grid: np.ndarray, duty: np.ndarray, upper: float) -> float:
    """Integral of `duty` over [0, upper], each interval integrated on its own.

    Kept because it is the obvious implementation and it is subtly wrong for
    this purpose: integrating each interval independently accumulates rounding
    error separately per interval, so two intervals that differ by almost no
    exposure can come back out of order by a few multiples of machine epsilon.
    Those are not counter-examples to the proof, they are artefacts of the
    arithmetic.  `--naive-integration` runs the Monte Carlo this way to show it.
    """
    mask = grid <= upper
    return float(np.trapezoid(duty[mask], grid[mask]))


def monte_carlo(
    rows: list[TypeARow],
    draws: int = 20_000,
    grid_points: int = 4_000,
    seed: int = 20260913,
    naive: bool = False,
) -> tuple[int, int, float, list[str]]:
    rng = np.random.default_rng(seed)
    horizon = max(r.p_wall_hours for r in rows)
    bounds = [r.p_wall_hours for r in rows]
    grid = build_grid(bounds, grid_points)

    violations = 0
    per_family: dict[str, int] = {f: 0 for f in DUTY_CYCLE_FAMILIES}
    ties = 0
    worst_relative = 0.0

    for i in range(draws):
        family = DUTY_CYCLE_FAMILIES[i % len(DUTY_CYCLE_FAMILIES)]
        duty = draw_duty_cycle(family, grid, rng)
        if naive:
            exposures = [integrate_to(grid, duty, b) for b in bounds]
        else:
            cumulative = cumulative_exposure(grid, duty)
            exposures = [exposure_at(grid, cumulative, b) for b in bounds]

        if not (exposures[0] <= exposures[1] <= exposures[2]):
            violations += 1
            per_family[family] += 1
            for lo, hi in ((exposures[0], exposures[1]), (exposures[1], exposures[2])):
                if lo > hi:
                    worst_relative = max(worst_relative, (lo - hi) / max(abs(hi), 1e-300))
        if exposures[0] == exposures[1] or exposures[1] == exposures[2]:
            ties += 1

    method = ("naive: each interval integrated independently"
              if naive else "cumulative: one running integral, bounds on the grid")
    lines = [
        f"  draws:                {draws:,}",
        f"  duty-cycle families:  {len(DUTY_CYCLE_FAMILIES)} ({', '.join(DUTY_CYCLE_FAMILIES)})",
        f"  grid points:          {grid.size:,} over {horizon:.4f} h",
        f"  integration:          {method}",
        f"  seed:                 {seed}",
        "",
        f"  ordering P_exp(A1) <= P_exp(A2) <= P_exp(A3) held in: "
        f"{(draws - violations) / draws:.2%} of draws ({draws - violations:,}/{draws:,})",
        f"  violations:           {violations}",
        f"  draws with a tie (an interval contributing zero extra exposure): {ties:,}",
    ]
    if violations:
        lines.append("  violations by family: "
                     + ", ".join(f"{k}={v}" for k, v in per_family.items() if v))
        lines.append(f"  largest relative violation: {worst_relative:.3e} "
                     f"(machine epsilon: {np.finfo(float).eps:.3e})")
        if worst_relative < 1e-12:
            lines.append("  -> these are floating-point artefacts, not counter-examples. See")
            lines.append("     integrate_to() for why, and run without --naive-integration.")
    return draws, violations, worst_relative, lines


# --- 3. where the nesting breaks --------------------------------------------

def nesting_break_demo(rows: list[TypeARow], seed: int = 20260913) -> list[str]:
    """A control applied at a different moment is not comparable this way.

    The corpus contains no such row - B_applied_nonnested is defined in the
    schema and empty in the data - so the counter-example below is explicitly
    hypothetical.  It exists to show what the argument does NOT cover.
    """
    rng = np.random.default_rng(seed + 1)
    lines: list[str] = []
    lines.append("  The corpus contains NO applied, non-nested control: every control other than")
    lines.append("  the 6 July rebuild was already standing. The following row is hypothetical and")
    lines.append("  is not part of the data set. It shows what the argument does not cover.")
    lines.append("")

    a1, a3 = rows[0], rows[2]
    # Hypothetical control applied 24 h after t0, reconstituted 1 h before A3.
    hyp_start = 24.0
    hyp_end = a3.p_wall_hours - 1.0
    lines.append(f"  hypothetical row H: applied t0 + {hyp_start:.0f} h, reconstituted t0 + {hyp_end:.2f} h")
    lines.append(f"  P_wall(H) = {hyp_end - hyp_start:.2f} h  >  P_wall(A1) = {a1.p_wall_hours:.2f} h")
    lines.append("")

    grid = build_grid([a1.p_wall_hours, a3.p_wall_hours, hyp_start, hyp_end], 4_000)
    reversals = 0
    draws = 5_000
    for i in range(draws):
        family = DUTY_CYCLE_FAMILIES[i % len(DUTY_CYCLE_FAMILIES)]
        duty = draw_duty_cycle(family, grid, rng)
        cumulative = cumulative_exposure(grid, duty)
        exp_a1 = exposure_at(grid, cumulative, a1.p_wall_hours)
        exp_h = (exposure_at(grid, cumulative, hyp_end)
                 - exposure_at(grid, cumulative, hyp_start))
        if exp_h < exp_a1:
            reversals += 1

    lines.append(f"  Over {draws:,} random duty cycles, P_exp(H) < P_exp(A1) in "
                 f"{reversals / draws:.1%} of draws ({reversals:,}/{draws:,}),")
    lines.append("  despite P_wall(H) being the larger of the two. With different start points the")
    lines.append("  ordering depends on the duty cycle, which is exactly what the nesting removes.")
    lines.append("  Interval-specific duty cycles would be required, and no data for them exists.")
    return lines


# --- 4. the parameter space of the wrong model ------------------------------

def alpha_model_parameter_space(rows: list[TypeARow]) -> list[str]:
    """The per-control alpha model, and why it is the wrong model here.

    A per-control model P_exp = alpha * P_wall, with an independent alpha for
    each control, would hold a rank reversal between A1 and A3 to be possible
    whenever alpha_A3 * P_wall_A3 < alpha_A1 * P_wall_A1.  Under nesting that
    scenario is not merely implausible, it is impossible: the A1 interval is
    contained in the A3 interval, so the same activity is being integrated over
    a subset.
    """
    a1, _, a3 = rows
    threshold = a1.p_wall_hours / a3.p_wall_hours

    lines = [
        "  Wrong model:  P_exp(i) = alpha_i * P_wall(i), with alpha_i independent per control.",
        "",
        f"  Under that model a rank reversal between {a1.row_id} and {a3.row_id} is 'possible' whenever",
        f"      alpha_{a3.row_id} < (P_wall({a1.row_id}) / P_wall({a3.row_id})) * alpha_{a1.row_id}",
        f"      alpha_{a3.row_id} < ({a1.p_wall_hours:.4f} / {a3.p_wall_hours:.4f}) * alpha_{a1.row_id}"
        f"  =  {threshold:.4f} * alpha_{a1.row_id}",
        "",
        "  Under nesting that region is empty. The alpha model is the wrong model for these",
        "  three rows precisely because it treats the three intervals as independent samples",
        "  of activity, when in fact the shorter interval is a subset of the longer one and",
        "  the SAME activity is being integrated. Evidence base 18.1, limitation 3.",
        "",
        f"  Ratio of the extremes: P_wall({a3.row_id}) / P_wall({a1.row_id}) = "
        f"{a3.p_wall_hours / a1.p_wall_hours:.4f}",
        "  This is a ratio of CALENDAR times. It is not a claim about exposure.",
    ]
    return lines


# --- report -----------------------------------------------------------------

CAVEATS = [
    "1. ONLY THE ORDERING IS SETTLED. The nesting establishes the rank of the three",
    "   P_exp values and nothing else. The magnitude - an originally suspected",
    "   shortening by roughly a factor of 15 - does NOT follow from it and remains",
    "   unsupported. It must be carried as OWN_RECONSTRUCTION, not as a result.",
    "",
    "2. THE PROOF HOLDS EXACTLY FOR THE THREE TYPE-A ROWS, the ones sharing the",
    "   6 July 01:16Z rebuild. It does not extend to the 9 July immediate bypass, to",
    "   the OpenAI-internal strand of 8-19 July (P1 chapter V), or to any standing",
    "   control. Those would need interval-specific duty cycles.",
    "",
    "3. NO PUBLIC DATA EXISTS on when evaluation workloads ran or paused between",
    "   6 and 7 July. P_exp is therefore NEVER to be reported as a point value -",
    "   only as a function or a range. Nothing in this module produces one, and",
    "   nothing in it should be read as producing one.",
]


def build_report(
    rows: list[TypeARow],
    draws: int,
    grid_points: int,
    seed: int,
    naive: bool = False,
) -> tuple[str, bool]:
    out: list[str] = []
    out.append(RULE)
    out.append("P_exp SENSITIVITY - the nesting argument and its parameter space")
    out.append(RULE)
    out.append("")

    out.append("The three type-A rows")
    out.append(THIN)
    for row in rows:
        out.append(f"  {row.row_id}  t0 = {row.applied.strftime('%Y-%m-%dT%H:%MZ')}   "
                   f"end = {row.reconstituted.strftime('%Y-%m-%dT%H:%MZ')}   "
                   f"P_wall = {row.p_wall_hours:>9.4f} h")
    out.append("")

    out.append("1. Nesting, verified from the data (not assumed)")
    out.append(THIN)
    nested, lines = verify_nesting(rows)
    out.extend(lines)
    out.append("")
    if nested:
        out.append("  The argument: P_exp is the integral of agent execution activity over the")
        out.append("  interval. Execution activity is nowhere negative. The integral of a")
        out.append("  non-negative function over a set cannot exceed its integral over a superset.")
        out.append("  Therefore P_exp(A1) <= P_exp(A2) <= P_exp(A3), for ANY duty-cycle function.")
        out.append("  This requires no data about when workloads ran. It is a proof, not an estimate.")
    else:
        out.append("  Nesting does NOT hold on the current data. Everything below is void.")
    out.append("")

    out.append("2. Monte Carlo demonstration - AN ILLUSTRATION OF THE PROOF, NOT A PROOF")
    out.append(THIN)
    out.append("  Nothing below adds evidence. The result above is deductive; random draws can")
    out.append("  only fail to contradict it. This section exists to make the claim tangible and")
    out.append("  to catch an implementation error in the integration.")
    out.append("")
    _, violations, _, mc_lines = monte_carlo(
        rows, draws=draws, grid_points=grid_points, seed=seed, naive=naive
    )
    out.extend(mc_lines)
    out.append("")

    out.append("3. Where the nesting breaks")
    out.append(THIN)
    out.extend(nesting_break_demo(rows, seed=seed))
    out.append("")

    out.append("4. Parameter space of the per-control alpha model")
    out.append(THIN)
    out.extend(alpha_model_parameter_space(rows))
    out.append("")

    out.append(RULE)
    out.append("LIMITATIONS - these travel with every use of this result")
    out.append(RULE)
    out.extend(CAVEATS)
    out.append("")
    out.append("Source: evidence base 18.1 (status: OWN_RECONSTRUCTION for the magnitude,")
    out.append("PROVABLE for the ordering) and 4.3 for the three P_wall values.")
    out.append(RULE)

    return "\n".join(out), nested and violations == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws", type=int, default=20_000, help="Monte Carlo draws")
    parser.add_argument("--grid-points", type=int, default=4_000, help="integration grid resolution")
    parser.add_argument("--seed", type=int, default=20260913, help="RNG seed")
    parser.add_argument("--out", type=Path, default=OUTPUT_TXT, help="where to write the report")
    parser.add_argument("--naive-integration", action="store_true",
                        help="integrate each interval independently, to show the round-off artefact")
    parser.add_argument("--quiet", action="store_true", help="write the file without printing")
    args = parser.parse_args(argv)

    rows = load_type_a()
    if len(rows) != 3:
        raise SystemExit(f"expected 3 type-A rows, found {len(rows)}")

    report, ok = build_report(
        rows, args.draws, args.grid_points, args.seed, naive=args.naive_integration
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report + "\n", encoding="utf-8")
    if not args.quiet:
        print(report)
        print()
        print(f"Written: {args.out}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
