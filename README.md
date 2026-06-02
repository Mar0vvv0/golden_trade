# A Share Strategy Backtester

Local A-share strategy backtesting workbench.

## What It Does

- Fetches A-share K-line data through public HTTP endpoints inspired by the local `a-stock-data` skill.
- Runs simple monthly or yearly rebalancing backtests.
- Shows equity curve, drawdown, trade periods, and per-symbol performance in a browser UI.
- Keeps fetched data in `data/cache/` to reduce repeated network calls.

## Run

```bash
cd /Users/marv/Desktop/codex/revert
python3 server.py
```

Then open:

```text
http://127.0.0.1:8765
```

## Current Strategies

- `equal_weight`: buy and hold the supplied stock pool with equal weights, rebalanced monthly or yearly.
- `momentum_top`: at each rebalance, choose the strongest stocks by recent return.

Your custom selection rules can be added in `strategies.py`. More advanced rules should use `strategy_pipeline.py`, which separates stock selection, buy rules, sell rules, stop-loss rules, and special-case handling.

## TongDaXin Formula Notes

If you provide TongDaXin selection formula code, keep the original formula text. The formula should be translated into Python in a reviewed step before it is used for backtesting, because TongDaXin functions and future-looking references can change the meaning of a strategy.

## Data Notes

This first version uses Baidu Stock Connect-style public K-line data for daily bars. Public data sources can fail, throttle, or change shape. Cached data is stored locally to make repeated backtests faster and more stable.
