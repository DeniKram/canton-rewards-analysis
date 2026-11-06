"""Load the Super Validator weights collected from Canton CIPs.

Output shapes:
    load_raw()          -> DataFrame (n_cips_rows, 6): cip, entity, weight, weight_type, status, note
    by_entity(df, ...)  -> DataFrame (n_entities, 2): entity, weight  (sorted desc)
"""
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sv_cips.csv"

# Scenarios for which rows count:
#   "fixed"    - only weights stated as a fixed number (or tier)
#   "max"      - fixed + "max weight" SVs taken at their maximum
#   "all_max"  - also outcome-linked SVs (USDT0, Mesh) at their maximum
SCENARIOS = {
    "fixed": {"fixed", "tier"},
    "max": {"fixed", "tier", "max"},
    "all_max": {"fixed", "tier", "max", "outcome_max"},
}


def load_raw(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["weight"] = pd.to_numeric(df["weight"], errors="coerce")
    return df


def by_entity(df: pd.DataFrame, scenario: str = "max") -> pd.DataFrame:
    """Sum weights per entity (Chainlink appears in two CIPs) for a scenario."""
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario!r}, use one of {list(SCENARIOS)}")
    mask = df["weight_type"].isin(SCENARIOS[scenario]) & df["weight"].notna()
    out = (
        df[mask]
        .groupby("entity", as_index=False)["weight"]
        .sum()
        .sort_values("weight", ascending=False, ignore_index=True)
    )
    return out


def unknown_weights(df: pd.DataFrame) -> list[str]:
    """Entities whose weight is not stated in the CIP title (DTCC, Nasdaq, ...)."""
    return df.loc[df["weight"].isna(), "entity"].tolist()
