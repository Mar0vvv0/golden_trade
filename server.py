from __future__ import annotations

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from backtester import run_backtest
from data_provider import get_many_daily_bars, normalize_code
from strategies import SCREEN_DETAILERS, STRATEGIES, list_strategies
from stock_universe import default_universe, universe_rows


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"


class Handler(SimpleHTTPRequestHandler):
    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._json({"ok": True, "service": "a-share-backtester"})
            return
        if parsed.path == "/api/strategies":
            self._json({"strategies": list_strategies()})
            return
        if parsed.path == "/api/universe":
            rows = universe_rows()
            self._json({"count": len(rows), "codes": [row["code"] for row in rows], "sample": rows[:20]})
            return
        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/screen":
            self._handle_screen()
            return
        if parsed.path == "/api/backtest":
            self._handle_backtest()
            return
        self._json({"error": "Not found"}, 404)

    def _read_json(self) -> dict:
        size = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(size).decode("utf-8"))

    def _handle_screen(self) -> None:
        try:
            payload = self._read_json()
            raw_codes = payload.get("codes") or payload.get("candidates") or default_universe()
            codes = [normalize_code(code) for code in raw_codes]
            if not codes:
                raise ValueError("Please configure the stock universe")
            start_date = payload.get("start_date")
            end_date = payload.get("end_date")
            if not start_date or not end_date:
                raise ValueError("start_date and end_date are required")
            strategy_id = payload.get("strategy", "equal_weight")
            strategy = STRATEGIES.get(strategy_id)
            if not strategy:
                raise ValueError(f"Unknown strategy: {strategy_id}")

            price_data = get_many_daily_bars(codes, start_date, end_date)
            selected = strategy(price_data, end_date, payload)
            detailer = SCREEN_DETAILERS.get(strategy_id)
            details = detailer(price_data, end_date, payload) if detailer else []
            self._json(
                {
                    "strategy": strategy_id,
                    "screen_date": end_date,
                    "stock_pool_count": len(codes),
                    "candidate_count": len(codes),
                    "loaded_count": len(price_data),
                    "selected_count": len(selected),
                    "selected_codes": selected,
                    "details": details,
                }
            )
        except Exception as exc:
            self._json({"error": str(exc)}, 400)

    def _handle_backtest(self) -> None:
        try:
            payload = self._read_json()
            raw_codes = payload.get("codes") or default_universe()
            codes = [normalize_code(code) for code in raw_codes]
            start_date = payload.get("start_date")
            end_date = payload.get("end_date")
            if not start_date or not end_date:
                raise ValueError("start_date and end_date are required")

            price_data = get_many_daily_bars(codes, start_date, end_date)
            result = run_backtest(price_data, payload)
            result["data_status"] = {
                "requested_codes": codes,
                "loaded_codes": list(price_data.keys()),
            }
            self._json(result)
        except Exception as exc:
            self._json({"error": str(exc)}, 400)

def main() -> None:
    port = 8765
    handler = lambda *args, **kwargs: Handler(*args, directory=str(STATIC), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"A-share backtester running at http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
