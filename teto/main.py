"""
Simple OHLC Backtester of Future.

TODO: ポジションバスケットクラスはwithで開けるようにしたら必ずsolveされるしいいんじゃないか。
"""

from __future__ import annotations

import dataclasses
import uuid
from typing import Literal


# class ContractProtocol:
#     pass

# class Side:
#     """
#     あとで導入。
#     """

#     def __init__(self, side: Literal['long', 'short']):
#         if side not in ['long', 'short']:
#             raise ValueError('Invalid side')

#         self.side = side
    
#     def reverse(self) -> Side:
#         if self.side == 'long':
#             return Side(side='short')
#         else:
#             return Side(side='long')


class MarketOrder:
    def __init__(self, size: float, price: float, side: Literal['long', 'short'], tp_price: float | None = None, sl_price: float | None = None) -> None:
        self.size = size
        self.price = price
        self.side = side
        self.tp_price = tp_price
        self.sl_price = sl_price

        self.id = uuid.uuid4()
        self.clock = 0

    def check_contract(self) -> bool:
        return True

    def generate_position(self) -> Position:
        return Position(
            size=self.size,
            price=self.price,
            side=self.side
        )
    
    def generate_tp_order(self) -> LimitOrder:
        side = 'short' if self.side == 'long' else 'long'

        return LimitOrder(
            size=self.size,
            price=self.tp_price,
            side=side
        )
    
    def generate_sl_order(self) -> StopOrder:
        side = 'short' if self.side == 'long' else 'long'

        return StopOrder(
            size=self.size,
            price=self.sl_price,
            side=side
        )
    
    # 関係し合っている2つのオーダーがあって、どちらかが約定したらもう片方をキャンセルといったような処理ができるようにする。


class LimitOrder:
    def __init__(self, size: float, price: float, side: Literal['long' , 'short'], tp_price: float | None = None, sl_price: float | None = None) -> None:
        self.size = size
        self.price = price
        self.side = side
        self.tp_price = tp_price
        self.sl_price = sl_price

        self.id = uuid.uuid4()
        self.clock = 0
    
    def check_contract(self, high_price: float, low_price: float) -> bool:
        
        if self.side == 'long' and self.price <= low_price:
            return True
        elif self.side == 'short' and self.price >= high_price:
            return True
        else:
            return False
    
    def generate_position(self) -> Position:
        return Position(
            size=self.size,
            price=self.price,
            side=self.side
        )
    
    def generate_tp_order(self) -> LimitOrder:
        side = 'short' if self.side == 'long' else 'long'

        return LimitOrder(
            size=self.size,
            price=self.tp_price,
            side=side
        )
    
    def generate_sl_order(self) -> StopOrder:
        side = 'short' if self.side == 'long' else 'long'

        return StopOrder(
            size=self.size,
            price=self.sl_price,
            side=side
        )


class StopOrder:
    def __init__(self, size: float, price: float, side: Literal['long', 'short'], tp_price: float | None = None, sl_price: float | None = None) -> None:
        self.size = size
        self.price = price
        self.side = side
        self.tp_price = tp_price
        self.sl_price = sl_price

        self.id = uuid.uuid4()
        self.clock = 0

    def check_triggering(self, high_price: float, low_price: float) -> bool:
        if self.side == 'long' and self.price >= high_price:
            return True
        elif self.side == 'short' and self.price <= low_price:
            return True
        else:
            return False
    
    def generate_market_order(self) -> MarketOrder:
        return MarketOrder(
            size=self.size,
            price=self.price,
            side=self.side,
            tp_price=self.tp_price,
            sl_price=self.sl_price
        )
        # 本来、クロックは入れたほうがいいが、今回は省略。処理場は問題ない。
    
    def generate_tp_order(self) -> LimitOrder:
        side = 'short' if self.side == 'long' else 'long'

        return LimitOrder(
            size=self.size,
            price=self.tp_price,
            side=side
        )
    
    def generate_sl_order(self) -> StopOrder:
        side = 'short' if self.side == 'long' else 'long'

        return StopOrder(
            size=self.size,
            price=self.sl_price,
            side=side
        )


class OrderBucket:
    def __init__(self, order: MarketOrder | LimitOrder | StopOrder | None = None) -> None:
        
        self.orders: list[tuple[int, MarketOrder | LimitOrder | StopOrder]] = []
        if order is not None:
            self.orders.append((0, order))

        # ↓ idはオーダーごとにuuidで振ることにしたので、不要になりました。
        # self.next_id = len(self.orders) # OrderのIDは0から始める。
            
    def add(self, order: MarketOrder | LimitOrder | StopOrder) -> None:
        self.orders.append((self.next_id, order))
        self.next_id += 1

    def solve(self, high_price: float, low_price: float) -> list[Position]:
        """
        Return the list of executed orders.
        """

        # 分離: クロックにより、処理するオーダーと処理しないオーダーに分離。
        # -> 処理しないオーダーは、次の処理に回す。
        processing_orders: list[tuple[int, MarketOrder | LimitOrder | StopOrder]] = []
        unprocessing_orders: list[tuple[int, MarketOrder | LimitOrder | StopOrder]] = []
        for o in self.orders:
            if o[1].clock > 0:
                processing_orders.append(o)
            else:
                unprocessing_orders.append(o)
        
        # 分離: StopOrderをMarketOrderに変換するため、StopOrderを分離したリストを作成。
        processing_orders_except_stop: list[tuple[int, MarketOrder | LimitOrder]] = []
        processing_stop_orders: list[tuple[int, StopOrder]] = []
        for o in processing_orders:
            if isinstance(o[1], StopOrder):
                processing_stop_orders.append(o)
            else:
                processing_orders_except_stop.append(o)

        # StopOrderの変換処理: StopOrderは、トリガーされたらMarketOrderに変換される。
        for o in processing_stop_orders:
            if o[1].check_triggering(high_price, low_price):
                mo = o[1].generate_market_order()
                processing_orders_except_stop.append((o[0], mo)) # IDは変更なし。
        
        # 約定判定処理
        # -> 約定したオーダーは、ポジションに変換し、リストに追加。
        # -> 未約定のオーダーは、次の処理に回す。
        contracted_orders: list[tuple[int, MarketOrder | LimitOrder]] = []
        uncontracted_orders: list[tuple[MarketOrder | LimitOrder]] = []
        for o in processing_orders_except_stop:
            if o[1].check_contract(high_price, low_price):
                contracted_orders.append(o)
            else:
                uncontracted_orders.append(o)
        
        # TP/SLオーダーの生成
        # -> 約定したオーダーの中に、TP/SLオーダーが設定されていたら、それを生成。
        # -> TP/SLオーダーには新しいidを振るので、最後に追加する。
        tp_sl_orders_without_id: list[MarketOrder | LimitOrder] = []
        for o in contracted_orders:
            if o[1].tp_price is not None:
                tp_order = o[1].generate_tp_order()
                tp_sl_orders_without_id.append(tp_order)
            
            if o[1].sl_price is not None:
                sl_order = o[1].generate_sl_order()
                tp_sl_orders_without_id.append(sl_order)
        
        # 次のオーダーをセット（未約定のもの）。

        # 未処理リストに未約定リストをエクステンドしたのち、クロックを進め、次に回す。

        return [o[1].generate_position() for o in contracted_orders]


# --- ポジション関係は完成 ---

class Position:
    def __init__(self, size: float, price: float, side: Literal['long', 'short']) -> None:
        self.size = size
        self.price = price
        self.side = side
    
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
    def __init__(self, long_position: Position | None = None, short_position: Position | None = None) -> None:

        # 初期ポジションがない場合は、殻のポジションを作成（ロング側）
        if long_position is None:
            self.pos_long = Position(size=0, price=0, side='long')
        else:
            self.pos_long = long_position
        
        # 初期ポジションがない場合は、殻のポジションを作成（ショート側）
        if short_position is None:
            self.pos_short = Position(size=0, price=0, side='short')
        else:
            self.pos_short = short_position

    def add(self, position: Position) -> None:
        if position.side == 'long':
            self.pos_long = self.pos_long.add(position)
        elif position.side == 'short':
            self.pos_short = self.pos_short.add(position)
        else:
            raise ValueError('Invalid side')
    
    def solve(self) -> SolvedTradingResult:
        """
        ポジションの解決と損益の計算。
        """

        if self.pos_long is None or self.pos_short is None:
            return SolvedTradingResult(size=0, pnl=0)
        elif self.pos_long.size == self.pos_short.size:

            # トレーディング・リザルトを作成
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

        elif self.pos_long.size > self.pos_short.size:

            result = SolvedTradingResult(
                size=self.pos_short.size,
                long_price = self.pos_long.price,
                short_price = self.pos_short.price,
                pnl = self.pos_short.size * (self.pos_short.price - self.pos_long.price)
            )

            # 更新
            self.pos_long.size -= self.pos_short.size # sizeだけが変わる
            self.pos_short = Position(size=0, price=0, side='short')

            return result

        elif self.pos_long.size < self.pos_short.size:
            result = SolvedTradingResult(
                size=self.pos_long.size,
                long_price = self.pos_long.price,
                short_price = self.pos_short.price,
                pnl = self.pos_long.size * (self.pos_short.price - self.pos_long.price)
            )
            # 更新
            self.pos_long = Position(size=0, price=0, side='long')
            self.pos_short.size -= self.pos_long.size

            return result


class SolvedTradingResult:
    def __init__(self, size: float, long_price: float, short_price: float, pnl: float) -> None:
        self.size = size
        self.long_price = long_price
        self.short_price = short_price
        self.pnl = pnl


# 簡易的なテスト
def test1():
    pos1 = Position(size=1, price=10000, side='long')
    pos2 = Position(size=1, price=12000, side='short')

    bucket = PositionBucket()
    bucket.add(pos1)
    bucket.add(pos2)



    result = bucket.solve()
    print(result.pnl)
    print(result.size)
    print(result.long_price)
    print(result.short_price)


if __name__ == '__main__':
    test1()