from __future__ import annotations

import uuid
from typing import Literal

from teto.order import BaseOrder, GenerativeOrder, MarketOrder, LimitOrder, OrderBucket
from teto.position import Position, PositionBucket
from teto.result import SolvedTradingResult


class Exchange:
    """
    Exchange.
    1. OrderBucketとPositionBucketの管理。
    2. 手数料の徴収。
    3. 各種計数のトラッキング。
    """
    def __init__(self, fee_rate_structure={MarketOrder: .0, LimitOrder: .0}) -> None:
        self.fee_rate_structure = fee_rate_structure

        # Initialize Buckets.
        self.order_bucket = OrderBucket()
        self.position_bucket = PositionBucket()

        # Initialize Tracker.
        self.fee_history: dict[uuid.UUID, float] = {}
    
    def __repr__(self):
        return f'Exchange(fee_rate_structure={self.fee_rate_structure})'
    
    def __str__(self):
        return f'Exchange(fee_rate_structure={self.fee_rate_structure})'

    def place(self, order: BaseOrder | GenerativeOrder) -> None:
        self.order_bucket.add(order)

    def place_many(self, orders: list[BaseOrder | GenerativeOrder]) -> None:
        for order in orders:
            self.place(order)
    
    def solve(self) -> None:
        # Orderの解決
        new_positions: list[tuple[BaseOrder, Position]] = self.order_bucket.solve()

        # 手数料の徴収
        for order, position in new_positions:
            fee = self.fee_rate_structure[type(order)] * position.size * position.price
            self.fee_history[order.id] = fee

        # Positionの追加
        for _, position in new_positions:
            self.position_bucket.add(position)

        # Positionの解決
        result: SolvedTradingResult = self.position_bucket.solve()

        # Trackerの更新
        pass
    
    @property
    def result(self):
        pass

