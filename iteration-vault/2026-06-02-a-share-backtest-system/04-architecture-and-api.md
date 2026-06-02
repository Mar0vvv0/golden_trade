# Architecture And API

## Architecture

- `server.py`: local HTTP server and JSON API.
- `data_provider.py`: A-share K-line fetching and local JSON cache.
- `backtester.py`: rebalance calendar, portfolio engine, metrics.
- `strategies.py`: pluggable strategy selection functions.
- `strategy_pipeline.py`: staged strategy contract for selection, entry, exit, stop-loss, and special-case rules.
- `static/`: browser UI.
- `data/cache/`: cached K-line JSON files.

## Strategy Pipeline

The backtest engine should evolve toward this order:

1. `select_candidates`: pick stocks first, possibly from TongDaXin formula code.
2. `should_enter`: decide whether and where to buy.
3. `should_exit`: decide whether and where to sell.
4. `should_stop_loss`: force risk exit.
5. `handle_special_case`: handle suspension, limit-up/down, ST, missing price, or custom exceptions.

Current MVP keeps the existing monthly/yearly rebalance mode for usability, but custom strategies should be implemented against this staged contract.

## API

### `GET /api/health`

Returns server status.

### `POST /api/backtest`

Request:

```json
{
  "codes": ["600519", "000001", "300750"],
  "start_date": "2022-01-01",
  "end_date": "2026-06-01",
  "frequency": "monthly",
  "strategy": "equal_weight",
  "initial_capital": 100000,
  "fee_bps": 5,
  "top_n": 3,
  "lookback_days": 60
}
```

Response:

```json
{
  "summary": {},
  "equity_curve": [],
  "drawdown_curve": [],
  "rebalance_log": [],
  "symbol_stats": []
}
```
