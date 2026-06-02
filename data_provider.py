from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import requests


UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
CACHE_DIR = Path(__file__).resolve().parent / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Bar:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float


def normalize_code(code: str) -> str:
    clean = code.strip().upper()
    clean = clean.replace(".SH", "").replace(".SZ", "").replace(".BJ", "")
    clean = clean.replace("SH", "").replace("SZ", "").replace("BJ", "")
    if len(clean) != 6 or not clean.isdigit():
        raise ValueError(f"Invalid A-share code: {code}")
    return clean


def _cache_path(code: str) -> Path:
    return CACHE_DIR / f"{normalize_code(code)}.json"


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _fetch_baidu_kline(code: str) -> list[Bar]:
    """Fetch daily K-lines using the Baidu endpoint documented in a-stock-data."""
    url = "https://finance.pae.baidu.com/selfselect/getstockquotation"
    params = {
        "all": "1",
        "isIndex": "false",
        "isBk": "false",
        "isBlock": "false",
        "isFutures": "false",
        "isStock": "true",
        "newFormat": "1",
        "group": "quotation_kline_ab",
        "finClientType": "pc",
        "code": code,
        "ktype": "1",
    }
    headers = {
        "User-Agent": UA,
        "Accept": "application/vnd.finance-web.v1+json",
        "Origin": "https://gushitong.baidu.com",
        "Referer": "https://gushitong.baidu.com/",
    }
    response = requests.get(url, params=params, headers=headers, timeout=20)
    response.raise_for_status()
    payload = response.json()
    result = payload.get("Result", {})
    market_data = result.get("newMarketData", {})
    keys = market_data.get("keys") or []
    rows = [row for row in (market_data.get("marketData") or "").split(";") if row]
    if not keys or not rows:
        raise RuntimeError(f"No K-line data returned for {code}")

    index = {name: idx for idx, name in enumerate(keys)}

    def get(parts: list[str], name: str, default: float = 0.0) -> float:
        idx = index.get(name)
        if idx is None or idx >= len(parts) or parts[idx] in ("", "-"):
            return default
        return float(parts[idx])

    bars: list[Bar] = []
    for row in rows:
        parts = row.split(",")
        time_idx = index.get("time", 0)
        if time_idx >= len(parts):
            continue
        raw_date = parts[time_idx]
        if len(raw_date) == 8 and raw_date.isdigit():
            day = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
        else:
            day = raw_date[:10]
        bars.append(
            Bar(
                date=day,
                open=get(parts, "open"),
                high=get(parts, "high"),
                low=get(parts, "low"),
                close=get(parts, "close"),
                volume=get(parts, "volume"),
                amount=get(parts, "amount"),
            )
        )
    bars.sort(key=lambda bar: bar.date)
    return bars


def _load_cache(code: str) -> list[Bar] | None:
    path = _cache_path(code)
    if not path.exists():
        return None
    # Refresh daily; this avoids hitting public endpoints on every page reload.
    if time.time() - path.stat().st_mtime > 24 * 60 * 60:
        return None
    data = json.loads(path.read_text())
    return [Bar(**item) for item in data]


def _save_cache(code: str, bars: Iterable[Bar]) -> None:
    path = _cache_path(code)
    path.write_text(
        json.dumps([bar.__dict__ for bar in bars], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_daily_bars(code: str, start_date: str, end_date: str, refresh: bool = False) -> list[dict]:
    code = normalize_code(code)
    bars = None if refresh else _load_cache(code)
    if bars is None:
        bars = _fetch_baidu_kline(code)
        _save_cache(code, bars)

    start = _parse_date(start_date)
    end = _parse_date(end_date)
    filtered = [bar for bar in bars if start <= _parse_date(bar.date) <= end and bar.close > 0]
    return [bar.__dict__ for bar in filtered]


def get_many_daily_bars(codes: list[str], start_date: str, end_date: str) -> dict[str, list[dict]]:
    result = {}
    errors = {}
    workers = max(1, int(os.environ.get("DATA_FETCH_WORKERS", "6")))

    def load_one(code: str) -> tuple[str, list[dict]]:
        normalized = normalize_code(code)
        return normalized, get_daily_bars(normalized, start_date, end_date)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(load_one, code): code for code in codes}
        for future in as_completed(futures):
            code = futures[future]
            try:
                normalized, bars = future.result()
                result[normalized] = bars
            except Exception as exc:
                errors[normalize_code(code)] = str(exc)
    if not result:
        raise RuntimeError(f"No usable price data. Errors: {errors}")
    return result
