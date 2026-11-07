"""Turn the raw CC Space JSON files into tidy tables and headline numbers.

Every function reads from data/raw/*.json (downloaded by fetch.py) and returns
a pandas object. Shapes are noted in each docstring.
"""
import json
from pathlib import Path

import pandas as pd

from metrics import summary

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


def _load(name: str) -> dict:
    return json.loads((RAW / f"{name}.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- price
def monthly_price() -> pd.Series:
    """Mean CC/USD price per month. Shape (n_months,), index = Period[M]."""
    p = pd.DataFrame(_load("cc_price_1y")["priceHistory"])
    p["month"] = pd.to_datetime(p["ts"], unit="ms").dt.to_period("M")
    return p.groupby("month")["price"].mean()


def latest_price() -> float:
    p = _load("cc_price_1y")["priceHistory"]
    return float(max(p, key=lambda r: r["ts"])["price"])


# ---------------------------------------------------------------- 1. liveness cliff
def liveness_monthly() -> pd.DataFrame:
    """Monthly liveness rewards. Shape (n_months, 4):
    cc_total, beneficiaries_avg, beneficiaries_max, cc_per_validator."""
    d = _load("liveness_cliff_all")
    p = pd.DataFrame(d["points"])
    p["month"] = pd.to_datetime(p["day"]).dt.to_period("M")
    g = p.groupby("month").agg(
        cc_total=("cc", "sum"),
        beneficiaries_avg=("beneficiaries", "mean"),
        beneficiaries_max=("beneficiaries", "max"),
    )
    g["cc_per_validator"] = g["cc_total"] / g["beneficiaries_avg"]
    return g


def liveness_meta() -> dict:
    d = _load("liveness_cliff_all")
    return {k: d[k] for k in ("cliffDate", "peakBeneficiaries", "totalCc")}


# ---------------------------------------------------------------- 2. rewards by type
GROUPS = {
    "Super Validators": ["sv"],
    "Applications": ["app", "featured_app_activity"],
    "Validators": ["validator", "validator_liveness", "validator_faucet"],
    "Other": ["development_fund", "unclaimed_activity"],
}


def rewards_monthly() -> pd.DataFrame:
    """Claimed rewards per month by group, in CC. Shape (n_months, 4), columns = GROUPS."""
    s = pd.DataFrame(_load("reward_activity_all")["series"])
    s["total_cc"] = s["total_cc"].astype(float)
    t = s.pivot_table(index="date", columns="reward_type", values="total_cc", aggfunc="sum").fillna(0)
    out = pd.DataFrame(index=t.index)
    for group, types in GROUPS.items():
        out[group] = t[[c for c in types if c in t.columns]].sum(axis=1)
    out.index = pd.PeriodIndex(out.index, freq="M")
    return out


def reward_shares(rew: pd.DataFrame, start: str, end: str) -> pd.Series:
    """Share of each group in claimed rewards over [start, end] months. Shape (4,)."""
    win = rew.loc[start:end].sum()
    return win / win.sum()


def mint_burn_monthly() -> pd.DataFrame:
    """Monthly minted and burned CC (data starts 2026-06). Shape (n_months, 2)."""
    m = pd.DataFrame(_load("mint_burn_all")["points"])
    m["month"] = pd.to_datetime(m["day"]).dt.to_period("M")
    g = m.groupby("month")[["minted", "burned"]].sum()
    return g[g["minted"] > 0]


# ---------------------------------------------------------------- 3. validators
def validators() -> pd.DataFrame:
    """All validators. Shape (n_validators, 9). Balances as float CC."""
    v = pd.DataFrame(_load("validators_balances")["validators"])
    for c in ("total_balance", "locked_balance", "unlocked_balance"):
        v[c] = v[c].astype(float)
    v["self_sponsored"] = v["sponsor"] == v["party_id"]
    return v


def validator_summary(v: pd.DataFrame) -> pd.DataFrame:
    """Per liveness state: count, share, median balance, share with ~zero balance. Shape (k, 4)."""
    g = v.groupby("liveness").agg(
        count=("party_id", "size"),
        median_balance=("total_balance", "median"),
        zero_balance_share=("total_balance", lambda x: (x < 1).mean()),
    )
    g["share"] = g["count"] / g["count"].sum()
    return g.sort_values("count", ascending=False)


# ---------------------------------------------------------------- 4. featured apps
def fa_compliance() -> pd.DataFrame:
    """Featured app reward weight vs allowance, last 30 days. Shape (n_providers, 10)."""
    f = pd.DataFrame(_load("fa_compliance_30d")["rows"])
    return f[["provider", "name", "weight", "usdSpent", "allowedWeight", "ratio",
              "status", "basis", "hostingType", "totalTransactions"]]


def fa_ratio_bins(f: pd.DataFrame) -> pd.Series:
    """How many apps sit in each reward-weight / allowance band. Shape (n_bins,)."""
    bins = [0, 0.5, 0.9, 1.0, 1.05, 1.10, 1.15, 1.20, 2.0, float("inf")]
    labels = ["<0.5", "0.5-0.9", "0.9-1.0", "1.00-1.05", "1.05-1.10", "1.10-1.15",
              "1.15-1.20", "1.2-2", ">2"]
    return pd.cut(f["ratio"].dropna(), bins, labels=labels).value_counts().sort_index()


def app_economics() -> pd.DataFrame:
    """Per application, last 30 days, CC. Shape (n_apps, 5)."""
    a = pd.DataFrame(_load("app_economics_30d")["rows"])
    a["rewards"] = a["appRewards"] + a["validatorRewards"]
    return a[["name", "appRewards", "validatorRewards", "syncFees", "rewards"]]


def fa_locking_summary() -> dict:
    """Lock status of APPROVED featured apps only.

    The API's own summary counts shortfalls over all 246 registry rows
    (paused, revoked and pending ones included), so it is not used here.
    """
    d = _load("fa_locking")
    a = pd.DataFrame(d["apps"])
    ap = a[a["status"] == "approved"]
    shortfall = ap["shortfall"].astype(float)
    return {
        "featured_count": int(len(ap)),
        "meets_requirement_count": int(ap["meets_requirement"].sum()),
        "shortfall_count": int((shortfall > 0).sum()),
        "shortfall_total": float(shortfall.sum()),
        "required_total": float(ap["required_lock"].astype(float).sum()),
        "paused_cip0116_count": int((a["status"] == "paused").sum()),
    }


# ---------------------------------------------------------------- 5. super validators
def sv_owners() -> pd.DataFrame:
    """Reward-right owners: name, kind (operator/hosted/escrow), weight, node. Shape (n_owners, 4)."""
    o = pd.DataFrame(_load("sv_rights")["owners"])
    return o[["name", "kind", "weight", "node_name"]]


def sv_nodes() -> pd.DataFrame:
    """Synchronizer nodes and the weight they carry. Shape (n_nodes, 6)."""
    n = pd.DataFrame(_load("sv_rights")["nodes"])
    return n[["name", "weight", "operator_weight", "hosted_weight", "escrow_weight", "owners"]] \
        .sort_values("weight", ascending=False, ignore_index=True)


# ---------------------------------------------------------------- headline numbers
def headline() -> dict:
    price = latest_price()
    live = liveness_monthly()
    rew = rewards_monthly()
    v = validators()
    f = fa_compliance()
    a = app_economics()
    nodes = sv_nodes()
    owners = sv_owners()
    lock = fa_locking_summary()
    mb = mint_burn_monthly()

    before = reward_shares(rew, "2025-01", "2025-12")
    after = reward_shares(rew, "2026-06", "2026-10")
    peak_month = live["cc_total"].idxmax()
    last_paid = live[live["cc_total"] > 0].index.max()
    full = mb.loc["2026-06":"2026-10"]

    return {
        "cc_price_usd": price,
        "liveness_cliff_date": liveness_meta()["cliffDate"],
        "liveness_peak_beneficiaries": int(live["beneficiaries_max"].max()),
        "liveness_peak_month": str(peak_month),
        "liveness_cc_per_validator_peak_month": float(live.loc[peak_month, "cc_per_validator"]),
        "liveness_cc_per_validator_last_paid_month": float(live.loc[last_paid, "cc_per_validator"]),
        "liveness_last_paid_month": str(last_paid),
        "reward_share_2025": before.round(3).to_dict(),
        "reward_share_jun_oct_2026": after.round(3).to_dict(),
        "validators_total": int(len(v)),
        "validators_by_state": v["liveness"].value_counts().to_dict(),
        "validators_self_sponsored": int(v["self_sponsored"].sum()),
        "validators_zero_balance_share": float((v["total_balance"] < 1).mean()),
        "burn_to_mint_jun_oct_2026": float(full["burned"].sum() / full["minted"].sum()),
        "fa_providers": int(len(f)),
        "fa_ratio_1.05_to_1.15": int(f["ratio"].between(1.05, 1.15).sum()),
        "fa_weight_concentration": {k: round(v_, 3) for k, v_ in summary(f["weight"][f["weight"] > 0]).items()},
        "apps_net_payers": int((a["syncFees"] > a["rewards"]).sum()),
        "apps_total": int(len(a)),
        "apps_rewards_30d_cc": float(a["rewards"].sum()),
        "apps_sync_fees_30d_cc": float(a["syncFees"].sum()),
        "fa_locking": lock,
        "sv_owner_concentration": {k: round(v_, 3) for k, v_ in summary(owners.groupby("name")["weight"].sum()).items()},
        "sv_node_concentration": {k: round(v_, 3) for k, v_ in summary(nodes["weight"]).items()},
        "sv_largest_node": {"name": nodes.loc[0, "name"],
                            "share": float(nodes.loc[0, "weight"] / nodes["weight"].sum()),
                            "owners_hosted": int(nodes.loc[0, "owners"])},
    }
