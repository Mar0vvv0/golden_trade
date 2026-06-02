from __future__ import annotations

import json
import time
from pathlib import Path

import requests


UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
ROOT = Path(__file__).resolve().parent
CACHE_PATH = ROOT / "data" / "cache" / "stock_universe.json"
CACHE_TTL = 24 * 60 * 60


def _load_cached_universe() -> list[dict] | None:
    if not CACHE_PATH.exists():
        return None
    if time.time() - CACHE_PATH.stat().st_mtime > CACHE_TTL:
        return None
    return json.loads(CACHE_PATH.read_text(encoding="utf-8"))


def _save_universe(rows: list[dict]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def _fetch_market_page(page: int) -> tuple[int, list[dict]]:
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": str(page),
        "pz": "100",
        "po": "1",
        "np": "1",
        "fltt": "2",
        "invt": "2",
        "fs": "m:1+t:2,m:1+t:23,m:0+t:6,m:0+t:80,m:0+t:81",
        "fields": "f2,f12,f13,f14,f20,f21",
    }
    last_error = None
    for attempt in range(4):
        try:
            response = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=20)
            response.raise_for_status()
            break
        except Exception as exc:
            last_error = exc
            time.sleep(1.0 + attempt * 0.8)
    else:
        raise RuntimeError(f"Market universe page {page} failed after retries: {last_error}")
    payload = response.json()
    data = payload.get("data") or {}
    return int(data.get("total") or 0), data.get("diff") or []


def refresh_universe() -> list[dict]:
    """Fetch the current A-share universe and cache active stocks locally."""
    total, first_page = _fetch_market_page(1)
    pages = max(1, (total + 99) // 100)
    raw_rows = list(first_page)
    for page in range(2, pages + 1):
        _total, rows = _fetch_market_page(page)
        raw_rows.extend(rows)
        time.sleep(0.15)

    seen = set()
    active_rows = []
    for item in raw_rows:
        code = str(item.get("f12") or "").strip()
        name = str(item.get("f14") or "").strip()
        if len(code) != 6 or not code.isdigit() or code in seen:
            continue
        if item.get("f2") in (None, "-") or item.get("f20") in (None, "-"):
            continue
        seen.add(code)
        active_rows.append(
            {
                "code": code,
                "name": name,
                "market": item.get("f13"),
                "price": item.get("f2"),
                "market_cap": item.get("f20"),
                "float_market_cap": item.get("f21"),
            }
        )

    if not active_rows:
        raise RuntimeError("No active A-share stocks returned from market universe endpoint")
    _save_universe(active_rows)
    return active_rows


def universe_rows(refresh: bool = False) -> list[dict]:
    if not refresh:
        cached = _load_cached_universe()
        if cached:
            return cached
    try:
        return refresh_universe()
    except Exception:
        cached = _load_cached_universe()
        if cached:
            return cached
        raise


def default_universe(refresh: bool = False) -> list[str]:
    return [row["code"] for row in universe_rows(refresh=refresh)]
