from __future__ import annotations

import math
from datetime import datetime

from strategies import STRATEGIES


def _parse(day: str):
    return datetime.strptime(day, "%Y-%m-%d").date()


def _all_trading_days(price_data: dict[str, list[dict]]) -> list[str]:
    days = sorted({bar["date"] for bars in price_data.values() for bar in bars})
    return days


def _close_lookup(price_data: dict[str, list[dict]]) -> dict[str, dict[str, float]]:
    return {
        code: {bar["date"]: float(bar["close"]) for bar in bars if float(bar["close"]) > 0}
        for code, bars in price_data.items()
    }


def _close_on_or_before(lookup: dict[str, float], day: str) -> float | None:
    if day in lookup:
        return lookup[day]
    eligible = [candidate for candidate in lookup.keys() if candidate <= day]
    if not eligible:
        return None
    return lookup[max(eligible)]


def _rebalance_days(days: list[str], frequency: str) -> list[str]:
    result = []
    last_key = None
    for day in days:
        parsed = _parse(day)
        key = (parsed.year, parsed.month) if frequency == "monthly" else (parsed.year,)
        if key != last_key:
            result.append(day)
            last_key = key
    return result


def _max_drawdown(equity_curve: list[dict]) -> tuple[float, list[dict]]:
    peak = -math.inf
    max_dd = 0.0
    curve = []
    for point in equity_curve:
        value = point["equity"]
        peak = max(peak, value)
        drawdown = value / peak - 1 if peak > 0 else 0
        max_dd = min(max_dd, drawdown)
        curve.append({"date": point["date"], "drawdown": drawdown})
    return max_dd, curve


def _annualized_return(total_return: float, start_date: str, end_date: str) -> float:
    days = max((_parse(end_date) - _parse(start_date)).days, 1)
    years = days / 365.25
    return (1 + total_return) ** (1 / years) - 1 if total_return > -1 else -1


def run_backtest(price_data: dict[str, list[dict]], config: dict) -> dict:
    if not price_data:
        raise ValueError("No price data")

    strategy_id = config.get("strategy", "equal_weight")
    strategy = STRATEGIES.get(strategy_id)
    if not strategy:
        raise ValueError(f"Unknown strategy: {strategy_id}")

    frequency = config.get("frequency", "monthly")
    if frequency not in ("monthly", "yearly"):
        raise ValueError("frequency must be monthly or yearly")

    initial_capital = float(config.get("initial_capital") or 100000)
    fee_bps = float(config.get("fee_bps") or 0)
    fee_rate = fee_bps / 10000

    days = _all_trading_days(price_data)
    if len(days) < 2:
        raise ValueError("Not enough trading days")

    lookup = _close_lookup(price_data)
    rebalance_set = set(_rebalance_days(days, frequency))
    holdings: dict[str, float] = {}
    cash = initial_capital
    equity_curve = []
    rebalance_log = []
    previous_equity = initial_capital
    positive_periods = 0
    completed_periods = 0

    for day in days:
        current_prices = {
            code: _close_on_or_before(code_lookup, day)
            for code, code_lookup in lookup.items()
        }
        current_prices = {code: price for code, price in current_prices.items() if price}
        equity = cash + sum(shares * current_prices.get(code, 0) for code, shares in holdings.items())

        if day in rebalance_set:
            selected = strategy(price_data, day, config)
            selected = [code for code in selected if current_prices.get(code)]
            if completed_periods > 0 and equity > previous_equity:
                positive_periods += 1
            if completed_periods > 0:
                rebalance_log[-1]["ending_equity"] = round(equity, 2)
                rebalance_log[-1]["period_return"] = round(equity / previous_equity - 1, 6)
            completed_periods += 1
            previous_equity = equity

            turnover_cost = equity * fee_rate if holdings or selected else 0
            equity_after_fee = max(equity - turnover_cost, 0)
            cash = 0.0
            holdings = {}
            if selected:
                target_value = equity_after_fee / len(selected)
                for code in selected:
                    holdings[code] = target_value / current_prices[code]
            else:
                cash = equity_after_fee

            rebalance_log.append(
                {
                    "date": day,
                    "selected": selected,
                    "equity": round(equity, 2),
                    "fee": round(turnover_cost, 2),
                }
            )
            equity = equity_after_fee

        equity_curve.append({"date": day, "equity": round(equity, 2)})

    final_equity = equity_curve[-1]["equity"]
    total_return = final_equity / initial_capital - 1
    max_dd, drawdown_curve = _max_drawdown(equity_curve)
    if rebalance_log:
        rebalance_log[-1]["ending_equity"] = round(final_equity, 2)
        rebalance_log[-1]["period_return"] = round(final_equity / previous_equity - 1, 6)

    symbol_stats = []
    for code, bars in price_data.items():
        first = bars[0]["close"] if bars else None
        last = bars[-1]["close"] if bars else None
        symbol_stats.append(
            {
                "code": code,
                "bars": len(bars),
                "start_price": first,
                "end_price": last,
                "return": round(last / first - 1, 6) if first and last else None,
            }
        )

    return {
        "summary": {
            "strategy": strategy_id,
            "frequency": frequency,
            "start_date": days[0],
            "end_date": days[-1],
            "initial_capital": initial_capital,
            "final_equity": round(final_equity, 2),
            "total_return": round(total_return, 6),
            "annualized_return": round(_annualized_return(total_return, days[0], days[-1]), 6),
            "max_drawdown": round(max_dd, 6),
            "rebalance_count": len(rebalance_log),
            "positive_period_rate": round(positive_periods / max(completed_periods - 1, 1), 6),
        },
        "equity_curve": equity_curve,
        "drawdown_curve": drawdown_curve,
        "rebalance_log": rebalance_log,
        "symbol_stats": symbol_stats,
    }
