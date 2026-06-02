# Ajie Python Strategy Integration

## Source

The user provided a Python class named `ZhuangGuStrategy`.

## Integration

Added `zhuang_gu_strategy.py` and changed `strategies.py` so `zhuang_n2_weekly` now uses this Python implementation.

## Important Differences From The Earlier TongDaXin Formula

- The Python draft uses `50 <= gain <= 300`, while the earlier TongDaXin text used `涨幅 >= 100 AND 涨幅 <= 300`.
- The Python draft finds the N1 high after the N1 low. This is closer to the user's intended "N1 low -> N1 high" structure.
- The Python draft includes stop-loss, take-profit targets, and position sizing.
- The app now returns screen details for this strategy through `/api/screen`.

## Current Status

This is still used primarily as a selection and signal module. The trade engine does not yet execute per-stock stop-loss or take-profit exits intraperiod.
