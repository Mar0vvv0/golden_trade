# 00 Intake

User wants an A-share strategy backtesting system placed under `/Users/marv/Desktop/codex/revert`.

Core requirement:
- User will later provide stock-selection strategies.
- System should backtest by month and year.
- Use `a-stock-data` where possible for A-share data.
- Present results with a frontend UI.

Assumption for MVP:
- Build a local web app with a Python backend and a browser frontend.
- Start with pluggable strategy scaffolding plus two example strategies.
- Use daily K-line data and rebalance monthly/yearly.
