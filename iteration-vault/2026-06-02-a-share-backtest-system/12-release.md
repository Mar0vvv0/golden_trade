# Release

## Delivered

- Local A-share backtesting web app.
- Python backend with `/api/backtest`, `/api/health`, and `/api/strategies`.
- K-line data provider using public daily bar endpoint and local JSON cache.
- Strategy plugin module with:
  - `equal_weight`
  - `momentum_top`
- Frontend dashboard with parameter form, metrics, equity curve, drawdown curve, rebalance log, and symbol stats.

## Verification

- Python syntax check passed:
  - `server.py`
  - `data_provider.py`
  - `backtester.py`
  - `strategies.py`
- Sample backtest passed with `600519` and `000001` for 2024.
- Local server started at `http://127.0.0.1:8765`.
- Health and strategy API checks passed.

## Next

Add custom user strategies in `strategies.py`, then expose strategy-specific parameters in the frontend.
