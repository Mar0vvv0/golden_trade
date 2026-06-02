# Strategy Model Update

## User Clarification

The user may provide strategy logic as TongDaXin stock-selection formula code.

The backtest flow should not stop at "select and rebalance". It should support:

1. stock selection
2. buy/entry rules
3. sell/exit rules
4. stop-loss rules
5. special-case handling

## Implementation Change

Added `strategy_pipeline.py` with a staged strategy contract:

- `select_candidates`
- `should_enter`
- `should_exit`
- `should_stop_loss`
- `handle_special_case`

Also added `TongDaXinFormulaSource` to preserve raw TongDaXin formula text before reviewed translation.

## Next Step

When the user provides a TongDaXin formula, translate it into a reviewed Python strategy class instead of executing arbitrary formula text directly.
