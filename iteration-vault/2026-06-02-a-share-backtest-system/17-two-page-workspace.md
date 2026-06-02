# Two Page Workspace

## User Request

Split the frontend into two project pages:

1. A strategy screening page that finds which stocks match the strategy today.
2. A strategy backtesting page that checks how the strategy performed over five years.

## Implementation

- Added page tabs:
  - `今日选股`
  - `策略回测`
- `今日选股` calls `/api/screen` with the selected strategy and screen date.
- `策略回测` calls `/api/backtest` with the candidate range as the historical universe.

## Important Modeling Correction

The backtest page does not use today's selected stocks as the five-year stock pool. That would create a future-looking test. Instead, it uses the candidate range as the universe and applies the strategy at each monthly/yearly rebalance point.

## Limitation

The app still requires a candidate range. Full A-share universe scanning needs a separate cached universe and batch screening system.
