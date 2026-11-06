"""Article charts from the CC Space data. One function = one PNG.

Palette: validated categorical slots (blue, orange, aqua, yellow). Aqua and
yellow are under 3:1 contrast on white, so every chart carries a legend or
direct labels, and the article includes the numbers as a table.
No dual axes: two measures with different units go into two panels.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, MUTED, GRID = "#1f2328", "#6b7280", "#e5e7eb"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
    "axes.titlelocation": "left", "axes.titlesize": 12, "axes.titleweight": "bold",
    "font.size": 9.5,
})


def _style(ax, grid_axis="y"):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis=grid_axis, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def _save(fig, out: Path, source: str = "Source: CC Space API (cc.itrocket.space), own calculations") -> Path:
    fig.text(0.01, 0.005, source, color=MUTED, fontsize=7.5)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(out, dpi=170)
    plt.close(fig)
    return out


def liveness_cliff(live: pd.DataFrame, cliff: str, out: Path) -> Path:
    """Two panels: validators receiving liveness rewards, and CC paid per validator."""
    x = live.index.to_timestamp()
    cliff_ts = pd.Timestamp(cliff)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.5, 6.2), sharex=True)

    a1.plot(x, live["beneficiaries_max"], color=BLUE, lw=2, marker="o", ms=4)
    a1.set_title("Validators receiving liveness rewards (monthly peak)")
    peak = live["beneficiaries_max"].idxmax()
    a1.annotate(f"{int(live.loc[peak, 'beneficiaries_max'])}", (peak.to_timestamp(), live.loc[peak, "beneficiaries_max"]),
                xytext=(-20, 6), textcoords="offset points", color=INK, fontsize=9)

    per_val = live["cc_per_validator"] / 1e3
    a2.plot(x, per_val, color=ORANGE, lw=2, marker="o", ms=4)
    a2.set_title("Liveness CC per validator per month, thousands")
    a2.set_ylabel("thousand CC")

    for ax in (a1, a2):
        ax.axvline(cliff_ts, color=MUTED, ls="--", lw=1)
        _style(ax)
    a1.text(cliff_ts, a1.get_ylim()[1] * 0.92, "  CIP-0096 cliff\n  30 Apr 2026", color=MUTED, fontsize=8.5, va="top")
    return _save(fig, out)


def rewards_by_type(rew: pd.DataFrame, out: Path) -> Path:
    """100% stacked bars: who receives newly claimed CC each month."""
    r = rew.loc["2025-01":"2026-10"]
    share = r.div(r.sum(axis=1), axis=0) * 100
    x = np.arange(len(share))
    colors = {"Super Validators": BLUE, "Applications": ORANGE, "Validators": AQUA, "Other": YELLOW}
    fig, ax = plt.subplots(figsize=(9, 4.6))
    bottom = np.zeros(len(share))
    for col in share.columns:
        ax.bar(x, share[col], bottom=bottom, color=colors[col], width=0.82,
               edgecolor=SURFACE, linewidth=1.2, label=col)
        bottom += share[col].to_numpy()
    ax.set_xticks(x[::2], [str(p) for p in share.index[::2]], rotation=45, ha="right")
    ax.set_ylim(0, 100)
    ax.set_ylabel("% of claimed rewards")
    ax.set_title("Who receives Canton Coin rewards, by month")
    ax.legend(ncol=4, frameon=False, loc="upper left", bbox_to_anchor=(0, -0.2))
    _style(ax)
    return _save(fig, out)


def validator_states(summ: pd.DataFrame, out: Path) -> Path:
    order = [s for s in ("active", "stale", "never_seen") if s in summ.index]
    s = summ.loc[order]
    fig, ax = plt.subplots(figsize=(7, 2.6))
    y = np.arange(len(s))[::-1]
    colors = [BLUE, ORANGE, MUTED][: len(s)]
    ax.barh(y, s["count"], color=colors, height=0.6)
    for yi, (state, row) in zip(y, s.iterrows()):
        ax.text(row["count"] + 10, yi,
                f"{int(row['count'])}  ({row['share']:.0%}), median balance {row['median_balance']:,.0f} CC",
                va="center", color=INK, fontsize=9)
    ax.set_yticks(y, s.index)
    ax.set_xlim(0, s["count"].max() * 1.9)
    ax.set_title("Canton validators by liveness state, Nov 2026")
    _style(ax, grid_axis="x")
    return _save(fig, out)


def fa_ratio_hist(bins: pd.Series, out: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    x = np.arange(len(bins))
    flagged = [lab in ("1.15-1.20", "1.2-2", ">2") for lab in bins.index]
    near_cap = [lab in ("1.05-1.10", "1.10-1.15") for lab in bins.index]
    colors = [ORANGE if f else (BLUE if n else "#9ec5f4") for f, n in zip(flagged, near_cap)]
    ax.bar(x, bins.values, color=colors, width=0.8)
    for xi, val in zip(x, bins.values):
        ax.text(xi, val + 0.4, str(val), ha="center", color=INK, fontsize=9)
    ax.set_xticks(x, bins.index)
    ax.set_xlabel("Reward weight / allowed weight (30 days)")
    ax.set_ylabel("Featured apps")
    ax.set_title("Featured apps cluster just below the 115% flag")
    ax.text(0.99, 0.95, "dark blue: 105-115%   orange: above 115% (flagged)",
            transform=ax.transAxes, ha="right", va="top", color=MUTED, fontsize=8.5)
    _style(ax)
    return _save(fig, out)


def app_rewards_vs_fees(a: pd.DataFrame, out: Path) -> Path:
    d = a[(a["rewards"] > 0) | (a["syncFees"] > 0)].copy()
    fig, ax = plt.subplots(figsize=(7, 6))
    xs = d["syncFees"].clip(lower=1e3)
    ys = d["rewards"].clip(lower=1e3)
    payer = d["syncFees"] > d["rewards"]
    ax.scatter(xs[~payer], ys[~payer], s=34, color=BLUE, edgecolor=SURFACE, lw=1, label="earns more than it pays")
    ax.scatter(xs[payer], ys[payer], s=34, color=ORANGE, edgecolor=SURFACE, lw=1, label="pays more than it earns")
    lim = [1e3, max(xs.max(), ys.max()) * 2]
    ax.plot(lim, lim, color=MUTED, ls="--", lw=1)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("Synchronizer fees paid, CC (30 days, log)")
    ax.set_ylabel("Rewards received, CC (30 days, log)")
    ax.set_title("Applications: rewards vs fees paid")
    for _, row in d.nlargest(5, "rewards").iterrows():
        ax.annotate(row["name"], (max(row["syncFees"], 1e3), max(row["rewards"], 1e3)),
                    xytext=(5, 3), textcoords="offset points", fontsize=8, color=INK)
    ax.text(lim[1] / 3, lim[1] / 1.6, "break-even", color=MUTED, fontsize=8, rotation=45)
    ax.legend(frameon=False, loc="lower right")
    _style(ax, grid_axis="both")
    return _save(fig, out)


def sv_nodes_chart(nodes: pd.DataFrame, out: Path) -> Path:
    """Stacked bars per synchronizer node: own (operator) vs hosted vs escrow weight."""
    n = nodes.copy()
    total = n["weight"].sum()
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    y = np.arange(len(n))[::-1]
    left = np.zeros(len(n))
    for col, color, label in (("operator_weight", BLUE, "own (operator)"),
                              ("hosted_weight", AQUA, "hosted for others"),
                              ("escrow_weight", YELLOW, "escrow for others")):
        vals = n[col] / total * 100
        ax.barh(y, vals, left=left, color=color, height=0.65, edgecolor=SURFACE, lw=1.2, label=label)
        left += vals.to_numpy()
    for yi, (_, row) in zip(y, n.iterrows()):
        ax.text(row["weight"] / total * 100 + 0.6, yi, f"{row['weight'] / total:.1%} · {int(row['owners'])} owners",
                va="center", color=INK, fontsize=8.5)
    ax.set_yticks(y, n["name"])
    ax.set_xlim(0, 62)
    ax.set_xlabel("% of total Super Validator reward weight")
    ax.set_title("Where Super Validator reward weight sits: 13 synchronizer nodes")
    ax.legend(frameon=False, loc="lower right")
    _style(ax, grid_axis="x")
    return _save(fig, out)
