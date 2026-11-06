"""Download the data for the Canton article from CC Space.

Usage:
    python fetch.py --dry-run        # shows what would be called and the cost, spends nothing
    python fetch.py                  # downloads, max 20 paid calls by default
    python fetch.py --max-calls 5    # stricter budget

Results land in data/raw/*.json. Re-running only fetches what is missing.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from client import RAW_DIR, BudgetExceeded, CCSpaceClient, load_api_key  # noqa: E402
from jobs import JOBS  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-calls", type=int, default=20)
    args = ap.parse_args()

    todo = [j for j in JOBS if not (RAW_DIR / f"{j[0]}.json").exists()]
    print(f"{len(JOBS)} jobs, {len(JOBS) - len(todo)} already cached, "
          f"{len(todo)} to fetch = {len(todo)} credits\n")
    for name, path, params, why in todo:
        print(f" - {name:22} {path} {params or ''}\n     {why}")

    if args.dry_run:
        print("\nDry run: nothing was requested.")
        return

    client = CCSpaceClient(load_api_key(), max_calls=args.max_calls)
    before = client.credits()
    print(f"\nCredits before: {before}\n")

    try:
        for name, path, params, _ in JOBS:
            client.get(name, path, params)
    except BudgetExceeded as e:
        print(f"\nStopped: {e}")
    finally:
        after = client.credits()
        print(f"\nPaid calls this run: {client.paid_calls}")
        print(f"Credits after:  {after}")
        print(f"Files in {RAW_DIR.relative_to(ROOT)}: "
              f"{len(list(RAW_DIR.glob('*.json')))}")


if __name__ == "__main__":
    main()
