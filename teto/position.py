"""
ポジションの管理を担当するモジュール。

"""

from __future__ import annotations
from typing import Literal


class Position:
    """
    Positionクラス。
    """

    def __init__(self, size: float, price: float, side: Literal['long', 'short']) -> None:
        self.size = size
        self.price = price
        self.side = side

    def __repr__(self):
        return f'Position(size={self.size}, price={self.price}, side={self.side})'
    
    def __str__(self):
        return f'Position(size={self.size}, price={self.price}, side={self.side})'
    
    def __eq__(self, other: Position) -> bool:
        return self.size == other.size and self.price == other.price and self.side == other.side
    
    def add(self, other: Position) -> Position:
        if self.side == other.side:
            return Position(
                size=self.size + other.size,
                price=(self.size * self.price + other.size * other.price) / (self.size + other.size), # 加重平均
                side=self.side
            )
        else:
            raise ValueError('Cannot add different side positions.')

class PositionBucket:
    """
    PositionBucketクラス。
    -> 現行ポジションの管理と解決に責任を持つ。
    """

    def __init__(self, long_position: Position | None = None, short_position: Position | None = None) -> None:

        # <-- INDEX: TODO --> Add validation.

        # Initialize.
        if long_position is None:
            self.pos_long = Position(size=0, price=0, side='long')
        else:
            self.pos_long = long_position
        
        if short_position is None:
            self.pos_short = Position(size=0, price=0, side='short')
        else:
            self.pos_short = short_position

    def add(self, position: Position) -> None:
        """
        ポジションの追加。
        
        """
        
        # <-- INDEX: TEST --> passed.
        if position.side == 'long':
            self.pos_long = self.pos_long.add(position)

        # <-- INDEX: TEST --> passed.
        elif position.side == 'short':
            self.pos_short = self.pos_short.add(position)
        else:
            raise ValueError('Invalid side')
    
    def solve(self) -> SolvedTradingResult:
        """
        ポジションの解決と損益の計算。

        """

        # <-- INDEX: TEST --> passed.
        if self.pos_long == Position(size=0, price=0, side='long') or self.pos_short == Position(size=0, price=0, side='short'):
            return SolvedTradingResult(size=0, long_price=0, short_price=0, pnl=0)
        
        # <-- INDEX: TEST --> passed.
        elif self.pos_long.size == self.pos_short.size:

            result = SolvedTradingResult(
                size=self.pos_long.size, # or self.pos_short.size
                long_price = self.pos_long.price,
                short_price = self.pos_short.price,
                pnl = self.pos_long.size * (self.pos_short.price - self.pos_long.price)
            )

            # 更新
            self.pos_long = Position(size=0, price=0, side='long')
            self.pos_short = Position(size=0, price=0, side='short')

            return result

        # <-- INDEX: TEST --> passed.
        elif self.pos_long.size > self.pos_short.size:

            result = SolvedTradingResult(
                size=self.pos_short.size,
                long_price = self.pos_long.price,
                short_price = self.pos_short.price,
                pnl = self.pos_short.size * (self.pos_short.price - self.pos_long.price)
            )

            self.pos_long.size -= self.pos_short.size
            self.pos_short = Position(size=0, price=0, side='short')

            return result

        # <-- INDEX: TEST --> passed.
        elif self.pos_long.size < self.pos_short.size:
            result = SolvedTradingResult(
                size=self.pos_long.size,
                long_price = self.pos_long.price,
                short_price = self.pos_short.price,
                pnl = self.pos_long.size * (self.pos_short.price - self.pos_long.price)
            )

            # 処理順を逆にしないように注意。
            self.pos_short.size -= self.pos_long.size
            self.pos_long = Position(size=0, price=0, side='long')

            return result


class SolvedTradingResult:
    def __init__(self, size: float, long_price: float, short_price: float, pnl: float) -> None:
        self.size = size
        self.long_price = long_price
        self.short_price = short_price
        self.pnl = pnl