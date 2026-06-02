from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


PriceMap = dict[str, list[dict]]


@dataclass
class StrategyContext:
    """Shared context passed through the staged strategy pipeline."""

    current_date: str
    price_data: PriceMap
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class TradeDecision:
    action: str
    code: str
    reason: str
    price: float | None = None
    weight: float | None = None


class StrategyPipeline(Protocol):
    """Contract for real strategies.

    The intended lifecycle is:
    1. select stocks
    2. decide entry
    3. decide exit
    4. apply stop-loss
    5. handle special cases
    """

    name: str

    def select_candidates(self, ctx: StrategyContext) -> list[str]:
        ...

    def should_enter(self, code: str, ctx: StrategyContext) -> TradeDecision | None:
        ...

    def should_exit(self, code: str, ctx: StrategyContext) -> TradeDecision | None:
        ...

    def should_stop_loss(self, code: str, ctx: StrategyContext) -> TradeDecision | None:
        ...

    def handle_special_case(self, code: str, ctx: StrategyContext) -> TradeDecision | None:
        ...


@dataclass
class TongDaXinFormulaSource:
    """Stores raw TongDaXin formula text before reviewed translation.

    TongDaXin formula syntax is not Python. Keep the raw formula as source text
    and translate it explicitly into a StrategyPipeline implementation.
    """

    name: str
    raw_formula: str
    notes: str = ""


class ManualPipelineStrategy:
    """Base class for strategies translated from user rules."""

    name = "manual_pipeline"

    def select_candidates(self, ctx: StrategyContext) -> list[str]:
        return list(ctx.price_data.keys())

    def should_enter(self, code: str, ctx: StrategyContext) -> TradeDecision | None:
        return TradeDecision(action="buy", code=code, reason="default equal entry")

    def should_exit(self, code: str, ctx: StrategyContext) -> TradeDecision | None:
        return None

    def should_stop_loss(self, code: str, ctx: StrategyContext) -> TradeDecision | None:
        return None

    def handle_special_case(self, code: str, ctx: StrategyContext) -> TradeDecision | None:
        return None
