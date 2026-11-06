"""Build all article numbers and charts from data/raw (run fetch.py first).

Run:  py -3.12 analyze.py
Writes outputs/headline.json, outputs/tables/*.csv and outputs/charts/*.png
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import analysis as A  # noqa: E402
import charts as C  # noqa: E402

OUT = ROOT / "outputs"
TABLES = OUT / "tables"
CHARTS = OUT / "charts"


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    CHARTS.mkdir(parents=True, exist_ok=True)

    live = A.liveness_monthly()
    rew = A.rewards_monthly()
    v = A.validators()
    vsum = A.validator_summary(v)
    f = A.fa_compliance()
    bins = A.fa_ratio_bins(f)
    apps = A.app_economics()
    nodes = A.sv_nodes()

    live.to_csv(TABLES / "liveness_monthly.csv")
    rew.to_csv(TABLES / "rewards_monthly_by_group.csv")
    vsum.to_csv(TABLES / "validators_by_state.csv")
    bins.to_csv(TABLES / "fa_ratio_bins.csv")
    f.sort_values("weight", ascending=False).to_csv(TABLES / "fa_compliance_30d.csv", index=False)
    apps.sort_values("rewards", ascending=False).to_csv(TABLES / "app_economics_30d.csv", index=False)
    nodes.to_csv(TABLES / "sv_nodes.csv", index=False)
    A.mint_burn_monthly().to_csv(TABLES / "mint_burn_monthly.csv")

    h = A.headline()
    (OUT / "headline.json").write_text(json.dumps(h, indent=2, default=str), encoding="utf-8")
    print(json.dumps(h, indent=2, default=str))

    for p in (
        C.liveness_cliff(live, h["liveness_cliff_date"], CHARTS / "1_liveness_cliff.png"),
        C.rewards_by_type(rew, CHARTS / "2_rewards_by_type.png"),
        C.validator_states(vsum, CHARTS / "3_validator_states.png"),
        C.fa_ratio_hist(bins, CHARTS / "4_fa_ratio_hist.png"),
        C.app_rewards_vs_fees(apps, CHARTS / "5_app_rewards_vs_fees.png"),
        C.sv_nodes_chart(nodes, CHARTS / "6_sv_nodes.png"),
    ):
        print("saved", p.relative_to(ROOT))


if __name__ == "__main__":
    main()
