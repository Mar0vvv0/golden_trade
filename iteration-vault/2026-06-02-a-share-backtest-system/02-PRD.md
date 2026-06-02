# PRD: A Share Strategy Backtesting System

## Goal

Create a local browser-based workbench for testing A-share stock-selection strategies over monthly or yearly rebalance periods.

## Target User

An investor who has stock-selection ideas but wants a visual, repeatable way to test whether those ideas worked historically.

## MVP Scope

- Input stock codes, start date, end date, initial capital, rebalance frequency, and strategy.
- Fetch daily close prices for each code.
- Run portfolio backtests with monthly or yearly rebalancing.
- Display summary metrics, equity curve, drawdown, holdings periods, and per-symbol returns.
- Keep strategy code modular so custom strategy rules can be added later.

## Strategy Model Update

The user's real strategy flow is staged:

1. Selection: first screen stocks from the A-share universe or a user-supplied pool.
2. Entry: after a stock is selected, apply buy rules.
3. Exit: after holding, apply sell rules.
4. Stop loss: apply hard or conditional stop-loss rules.
5. Special handling: apply exceptions such as limit-up/limit-down, suspension, ST filtering, one-word board behavior, or other user-defined cases.

The user may provide selection logic as TongDaXin formula code. The system should preserve the raw formula, translate it carefully, and only execute after the translated rule is reviewed.

## Not In MVP

- Full-market stock universe scanning.
- Minute data.
- Transaction cost modeling beyond a simple fee/slippage setting.
- Survivorship-bias correction.
- Professional-grade corporate action adjustment.

## Acceptance

- User can run `python3 server.py`.
- Browser opens a usable dashboard.
- A sample backtest can run for several A-share codes.
- Results show total return, annualized return, max drawdown, win rate, and selected holdings.
- Strategy code can be organized as a pipeline instead of one monolithic function.
