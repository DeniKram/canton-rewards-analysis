"""Charts for the article. Each function saves one PNG and returns its path."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from metrics import lorenz, shares

INK = "#1f2933"
MUTED = "#8a94a6"
ACCENT = "#2f6fdf"
WARN = "#d9480f"


def _style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(MUTED)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=9)


def weights_bar(ent: pd.DataFrame, out: Path) -> Path:
    """Horizontal bars, one per SV, sorted by weight. ent shape (n, 2)."""
    s = shares(ent["weight"]) * 100
    fig, ax = plt.subplots(figsize=(8, max(4, 0.22 * len(ent))))
    y = np.arange(len(ent))[::-1]
    ax.barh(y, s, color=ACCENT, height=0.7)
    ax.set_yticks(y, ent["entity"])
    ax.set_xlabel("Share of announced SV weight, %")
    ax.set_title("Canton Super Validators by announced weight", loc="left", color=INK)
    _style(ax)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def lorenz_plot(ent: pd.DataFrame, out: Path) -> Path:
    x, y = lorenz(ent["weight"])
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.plot([0, 1], [0, 1], color=MUTED, ls="--", lw=1, label="perfect equality")
    ax.plot(x, y, color=ACCENT, lw=2, label="Canton SVs")
    ax.fill_between(x, y, x, color=ACCENT, alpha=0.08)
    ax.set_xlabel("Share of Super Validators (smallest first)")
    ax.set_ylabel("Share of total weight")
    ax.set_title("Lorenz curve of SV weight", loc="left", color=INK)
    ax.legend(frameon=False)
    _style(ax)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def growth_plot(raw: pd.DataFrame, out: Path) -> Path:
    """Cumulative announced weight and SV count in CIP order (CIP number as time proxy)."""
    d = raw.dropna(subset=["weight"]).sort_values("cip")
    cum_w = d["weight"].cumsum().to_numpy()
    cum_n = np.arange(1, len(d) + 1)
    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    ax1.step(d["cip"], cum_w, where="post", color=ACCENT, lw=2, label="cumulative weight")
    ax1.set_xlabel("CIP number (proxy for time)")
    ax1.set_ylabel("Cumulative announced weight", color=ACCENT)
    ax2 = ax1.twinx()
    ax2.step(d["cip"], cum_n, where="post", color=WARN, lw=1.5, label="number of SV entries")
    ax2.set_ylabel("Number of SV entries", color=WARN)
    ax2.spines["top"].set_visible(False)
    ax1.axvline(96, color=MUTED, ls=":", lw=1)
    ax1.text(96.5, cum_w.max() * 0.05, "CIP-0096\nliveness rewards removed", color=MUTED, fontsize=8)
    ax1.set_title("Super Validator set growth through governance", loc="left", color=INK)
    _style(ax1)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out
