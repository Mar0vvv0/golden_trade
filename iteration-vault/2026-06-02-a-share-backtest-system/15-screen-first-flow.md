# Screen First Flow

## User Correction

The user clarified that the stock pool must be produced by the selected strategy. The UI should not treat a manually entered list as the final stock pool.

## Implementation

- Added `/api/screen`.
- Renamed the manual list in the UI to candidate range.
- Added a screen button: "先按策略选股".
- Added a readonly selected pool field.
- Backtest now uses selected stocks, not the original candidate list.

## Current Limitation

The first version still requires a candidate range because scanning all A-shares through public endpoints would be slow and may trigger throttling. A later version should add a cached full-market universe and batch screening.
