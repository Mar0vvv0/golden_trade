from __future__ import annotations


class ZhuangGuStrategy:
    """庄股形态战法 - 阿杰老师.

    This is adapted from the user's Python draft. It works with the local app's
    weekly bar dictionaries instead of yfinance/pandas DataFrames.
    """

    def __init__(self, weekly_data: list[dict], stock_code: str):
        self.weekly = weekly_data
        self.code = stock_code
        self.current_price = weekly_data[-1]["close"] if weekly_data else 0

    def check_n2_selection(self) -> tuple[bool, dict]:
        """庄股 N2 混沌期选股公式 - 周线适用 - 放宽版."""
        w = self.weekly
        if len(w) < 60:
            return False, {"error": "数据不足60周"}

        lookback = min(40, len(w))
        start = len(w) - lookback
        recent = w[-lookback:]

        n1_low_rel = min(range(len(recent)), key=lambda idx: recent[idx]["low"])
        n1_low_idx = start + n1_low_rel
        n1_low = w[n1_low_idx]["low"]

        after_low = w[n1_low_idx:]
        n1_high_rel = max(range(len(after_low)), key=lambda idx: after_low[idx]["high"])
        n1_high_idx = n1_low_idx + n1_high_rel
        n1_high = w[n1_high_idx]["high"]

        gain = (n1_high - n1_low) / n1_low * 100 if n1_low else 0
        segment_broken = 50 <= gain <= 300

        n2_weeks = len(w) - n1_high_idx - 1
        after_n1_high = w[n1_high_idx:]
        max_drawdown = (
            (n1_high - min(bar["low"] for bar in after_n1_high)) / n1_high * 100
            if n1_high and after_n1_high
            else 100
        )
        drawdown_ok = max_drawdown < 50

        n1_range = n1_high - n1_low
        golden_382 = n1_low + n1_range * 0.382
        price_in_zone = golden_382 * 0.95 <= self.current_price <= golden_382 * 1.05

        n2_data = w[n1_high_idx + 1 :]
        if len(n2_data) >= 5:
            n2_avg_vol = sum(bar.get("volume", 0) for bar in n2_data) / len(n2_data)
            before_n1 = w[max(0, n1_high_idx - 20) : n1_high_idx]
            n1_avg_vol = (
                sum(bar.get("volume", 0) for bar in before_n1) / len(before_n1)
                if before_n1
                else n2_avg_vol
            )
            volume_ok = n2_avg_vol <= n1_avg_vol * 1.2
        else:
            volume_ok = True

        is_pass = segment_broken and 16 <= n2_weeks <= 60 and drawdown_ok and price_in_zone

        details = {
            "n1_low": round(n1_low, 2),
            "n1_high": round(n1_high, 2),
            "gain_pct": round(gain, 1),
            "segment_broken": segment_broken,
            "n2_weeks": n2_weeks,
            "max_drawdown_pct": round(max_drawdown, 1),
            "drawdown_ok": drawdown_ok,
            "golden_382": round(golden_382, 2),
            "current_price": round(self.current_price, 2),
            "price_in_zone": price_in_zone,
            "volume_ok": volume_ok,
            "is_pass": is_pass,
        }
        return is_pass, details

    def get_golden_levels(self, n1_low: float, n1_high: float) -> dict[str, float]:
        diff = n1_high - n1_low
        return {
            "0.191": n1_low + diff * 0.191,
            "0.382": n1_low + diff * 0.382,
            "0.5": n1_low + diff * 0.5,
            "0.618": n1_low + diff * 0.618,
            "1.382": n1_high + diff * 0.382,
        }

    def buy_signal(self, method: str = "golden") -> tuple[bool, str]:
        is_pass, details = self.check_n2_selection()
        if not is_pass:
            return False, f"选股未通过: {details.get('error', '条件不足')}"

        if method == "golden":
            if details["price_in_zone"]:
                return True, f"黄金分割买点激活 | 现价{details['current_price']} @0.382区域"
            return False, f"等待价格进入0.382区域 | 当前{details['current_price']} 目标{details['golden_382']}"

        if method == "pull":
            return False, "日线拉升法需要额外日线数据"

        return False, "无买点"

    def stop_loss_price(self, details: dict) -> float:
        levels = self.get_golden_levels(details["n1_low"], details["n1_high"])
        return levels["0.191"]

    def take_profit_targets(self, details: dict) -> dict[str, float]:
        levels = self.get_golden_levels(details["n1_low"], details["n1_high"])
        return {
            "min_target": levels["0.382"],
            "mid_target": levels["0.618"],
            "max_target": levels["1.382"],
        }

    def position_size(
        self,
        total_capital: float = 100000,
        risk_per_trade: float = 0.02,
        entry_price: float | None = None,
        stop_price: float | None = None,
    ) -> float:
        if entry_price is None or stop_price is None:
            return 0.1
        stop_loss_pct = abs(entry_price - stop_price) / entry_price
        if stop_loss_pct <= 0:
            return 0.1
        max_loss = total_capital * risk_per_trade
        position_value = max_loss / stop_loss_pct
        return min(position_value / total_capital, 0.3)

    def full_signal(self, total_capital: float = 100000) -> dict:
        is_pass, details = self.check_n2_selection()
        if not is_pass:
            return {"signal": "HOLD", "code": self.code, "reason": "选股条件不通过", "details": details}

        buy, buy_msg = self.buy_signal(method="golden")
        if not buy:
            return {"signal": "WAIT", "code": self.code, "reason": buy_msg, "details": details}

        stop_loss = self.stop_loss_price(details)
        targets = self.take_profit_targets(details)
        position = self.position_size(total_capital, entry_price=self.current_price, stop_price=stop_loss)

        return {
            "signal": "BUY",
            "code": self.code,
            "entry_price": self.current_price,
            "stop_loss": round(stop_loss, 2),
            "targets": {key: round(value, 2) for key, value in targets.items()},
            "position_ratio": round(position, 2),
            "risk_per_trade": "2% of capital",
            "reason": buy_msg,
            "details": details,
        }
