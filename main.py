"""Compute concentration of Canton Super Validator weight from public CIPs.

Run:  python main.py
Writes outputs/metrics.csv and outputs/*.png
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from load import SCENARIOS, by_entity, load_raw, unknown_weights  # noqa: E402
from metrics import summary  # noqa: E402
from plots import growth_plot, lorenz_plot, weights_bar  # noqa: E402

OUT = ROOT / "outputs"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    raw = load_raw()
    print(f"CIP rows: {len(raw)}  |  weight unknown: {', '.join(unknown_weights(raw))}\n")

    rows = []
    for name in SCENARIOS:
        ent = by_entity(raw, name)
        rows.append({"scenario": name, **summary(ent["weight"])})
    table = pd.DataFrame(rows).set_index("scenario")
    table.to_csv(OUT / "metrics.csv")
    with pd.option_context("display.float_format", "{:.3f}".format, "display.width", 140):
        print(table.T)

    ent = by_entity(raw, "max")
    print("\nTop 10 (scenario 'max'):")
    print(ent.head(10).to_string(index=False))

    for p in (
        weights_bar(ent, OUT / "sv_weights_bar.png"),
        lorenz_plot(ent, OUT / "sv_lorenz.png"),
        growth_plot(raw, OUT / "sv_growth.png"),
    ):
        print("saved", p.relative_to(ROOT))


if __name__ == "__main__":
    main()
