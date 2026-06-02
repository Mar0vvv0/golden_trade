from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from zhuang_gu_strategy import ZhuangGuStrategy


PriceMap = dict[str, list[dict]]
StrategyFn = Callable[[PriceMap, str, dict], list[str]]


def _close_on_or_before(bars: list[dict], day: str) -> float | None:
    selected = None
    for bar in bars:
        if bar["date"] <= day:
            selected = bar
        else:
            break
    return selected["close"] if selected else None


def _weekly_bars_until(bars: list[dict], day: str) -> list[dict]:
    weeks: dict[tuple[int, int], dict] = {}
    for bar in bars:
        if bar["date"] > day:
            break
        parsed = datetime.strptime(bar["date"], "%Y-%m-%d").date()
        key = parsed.isocalendar()[:2]
        if key not in weeks:
            weeks[key] = {
                "date": bar["date"],
                "open": bar["open"],
                "high": bar["high"],
                "low": bar["low"],
                "close": bar["close"],
                "volume": bar.get("volume", 0),
            }
        else:
            weeks[key]["high"] = max(weeks[key]["high"], bar["high"])
            weeks[key]["low"] = min(weeks[key]["low"], bar["low"])
            weeks[key]["close"] = bar["close"]
            weeks[key]["date"] = bar["date"]
            weeks[key]["volume"] += bar.get("volume", 0)
    return list(weeks.values())


def _barslast(values: list[float], target: float) -> int:
    for offset, value in enumerate(reversed(values)):
        if value == target:
            return offset
    return len(values)


def equal_weight(price_data: PriceMap, rebalance_date: str, params: dict) -> list[str]:
    return [code for code, bars in price_data.items() if _close_on_or_before(bars, rebalance_date)]


def zhuang_n2_weekly(price_data: PriceMap, rebalance_date: str, params: dict) -> list[str]:
    """庄股 N2 混沌期选股, using the user's Python strategy draft."""
    selected = []
    for code, daily_bars in price_data.items():
        weekly = _weekly_bars_until(daily_bars, rebalance_date)
        if not weekly or weekly[-1]["close"] <= 0 or weekly[-1].get("volume", 0) <= 0:
            continue
        strategy = ZhuangGuStrategy(weekly, code)
        is_pass, _details = strategy.check_n2_selection()
        if is_pass:
            selected.append(code)
    return selected


def zhuang_n2_weekly_details(price_data: PriceMap, rebalance_date: str, params: dict) -> list[dict]:
    rows = []
    for code, daily_bars in price_data.items():
        weekly = _weekly_bars_until(daily_bars, rebalance_date)
        if not weekly:
            rows.append({"code": code, "is_pass": False, "error": "无周线数据"})
            continue
        strategy = ZhuangGuStrategy(weekly, code)
        signal = strategy.full_signal(float(params.get("initial_capital") or 100000))
        details = signal.get("details", {})
        rows.append(
            {
                "code": code,
                "signal": signal.get("signal"),
                "reason": signal.get("reason"),
                "is_pass": bool(details.get("is_pass")),
                "n1_low": details.get("n1_low"),
                "n1_high": details.get("n1_high"),
                "gain_pct": details.get("gain_pct"),
                "n2_weeks": details.get("n2_weeks"),
                "max_drawdown_pct": details.get("max_drawdown_pct"),
                "golden_382": details.get("golden_382"),
                "current_price": details.get("current_price"),
                "price_in_zone": details.get("price_in_zone"),
                "stop_loss": signal.get("stop_loss"),
                "targets": signal.get("targets"),
                "position_ratio": signal.get("position_ratio"),
                "error": details.get("error"),
            }
        )
    return rows


STRATEGIES: dict[str, StrategyFn] = {
    "equal_weight": equal_weight,
    "zhuang_n2_weekly": zhuang_n2_weekly,
}

SCREEN_DETAILERS = {
    "zhuang_n2_weekly": zhuang_n2_weekly_details,
}


def list_strategies() -> list[dict]:
    return [
        {
            "id": "equal_weight",
            "name": "等权股票池",
            "description": "每次调仓都买入输入股票池中有价格数据的全部股票。",
        },
        {
            "id": "zhuang_n2_weekly",
            "name": "庄股 N2 混沌期",
            "description": "按你的通达信周线公式筛选 N2 调整期、回撤可控、接近 0.382 黄金分割区域的股票。",
        },
        {
            "id": "custom_pipeline",
            "name": "自定义交易流水线",
            "description": "预留给通达信选股公式、买点、卖点、止损和特殊情况规则。先在 strategy_pipeline.py 中实现后再启用。",
        },
    ]
