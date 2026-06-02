# Development Rules

- Keep the app local-first and dependency-light.
- Do not call Eastmoney in parallel; public APIs can throttle.
- Cache K-line data in `data/cache/`.
- Keep strategies as pure functions that receive price history and return selected codes.
- Prefer readable output over quant-library cleverness.
