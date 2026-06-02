# Zhuang N2 Weekly Formula

## Raw Formula

Stored at `strategy-formulas/zhuang_n2_weekly.tdx`.

## Translation Notes

- The formula is weekly.
- The current app fetches daily bars, so the Python implementation aggregates daily bars into weekly OHLCV bars first.
- The final condition uses `涨幅 >= 100 AND 涨幅 <= 300` because that is what the code says, even though the comment mentions `50%~300%`.
- `N1高点有效` is calculated in the formula but not used in the final `选股` expression. The Python implementation keeps the final expression faithful and does not add this condition.
- `缩量调整` is calculated but marked optional and not used in the final `选股` expression. The Python implementation does not require it.
- `DYNAINFO(9) > 0` means excluding suspended stocks. In this local backtest, this is approximated by requiring a usable latest close and volume.

## Current Role

This formula is implemented as a selection rule only. Buy, sell, stop-loss, and special-case execution rules will be added later through `strategy_pipeline.py`.

## Implementation

Implemented in `strategies.py` as `zhuang_n2_weekly`.

The frontend strategy selector now includes `庄股 N2 混沌期`.

## Verification

- Python syntax check passed.
- Sample backtest ran with `600519`, `000001`, `300750`, and `688017` from 2023-01-01 to 2026-06-01.
- Local server was restarted and `/api/strategies` includes `zhuang_n2_weekly`.
