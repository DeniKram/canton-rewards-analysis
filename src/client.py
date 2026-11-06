"""Minimal CC Space API client with an on-disk cache and a hard call budget.

- The API key is read from the CC_SPACE_API_KEY environment variable or from a
  local .env file (never hard-code it, never commit .env).
- Every successful response is saved to data/raw/<name>.json. If that file
  already exists, the cached copy is returned and NO credit is spent.
- `max_calls` stops the run before it can spend more than you allowed.
"""
import json
import os
import time
from pathlib import Path

import requests

BASE_URL = "https://cc-api.itrocket.space"
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"


def load_api_key() -> str:
    key = os.environ.get("CC_SPACE_API_KEY")
    env_file = ROOT / ".env"
    if not key and env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("CC_SPACE_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        raise SystemExit(
            "No API key. Create a file named .env next to fetch.py with one line:\n"
            "CC_SPACE_API_KEY=cs_live_your_key_here"
        )
    return key


class BudgetExceeded(RuntimeError):
    pass


class CCSpaceClient:
    def __init__(self, api_key: str, max_calls: int, timeout: int = 60):
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
        )
        self.max_calls = max_calls
        self.paid_calls = 0
        self.timeout = timeout
        RAW_DIR.mkdir(parents=True, exist_ok=True)

    def _request(self, path: str, params: dict | None = None) -> requests.Response:
        url = BASE_URL + path
        for attempt in range(4):
            resp = self.session.get(url, params=params, timeout=self.timeout)
            if resp.status_code == 429:  # rate limited
                wait = int(resp.headers.get("Retry-After", "5"))
                print(f"   429 rate limited, waiting {wait}s")
                time.sleep(wait)
                continue
            if resp.status_code == 502 and attempt < 3:  # upstream hiccup, safe to retry
                time.sleep(3 * (attempt + 1))
                continue
            return resp
        return resp

    def credits(self) -> dict:
        """Free call: current credit balance."""
        resp = self._request("/api/v1/credits/balance")
        resp.raise_for_status()
        return resp.json()

    def get(self, name: str, path: str, params: dict | None = None, free: bool = False) -> dict:
        cache = RAW_DIR / f"{name}.json"
        if cache.exists():
            print(f"   cached  {name}")
            return json.loads(cache.read_text(encoding="utf-8"))

        if not free and self.paid_calls >= self.max_calls:
            raise BudgetExceeded(f"budget of {self.max_calls} paid calls reached, stopping")

        resp = self._request(path, params)
        if resp.status_code == 401:
            raise SystemExit("401: API key missing, malformed or revoked. Check .env")
        if resp.status_code == 402:
            raise SystemExit("402: out of credits. Stopping, nothing else will be spent.")
        resp.raise_for_status()

        if not free:
            self.paid_calls += 1
        data = resp.json()
        cache.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"   fetched {name}  (paid calls this run: {self.paid_calls})")
        return data
